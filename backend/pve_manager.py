import os
from proxmoxer import ProxmoxAPI
from typing import Dict, Optional
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

class PVEManager:
    def __init__(self):
        import logging
        self.logger = logging.getLogger(__name__)
        self.pve_nodes = os.getenv('PVE_NODES', 'pve1,pve2,pve3,pve4').split(',')
        self.pve_user = os.getenv('PVE_USER')
        self.pve_password = os.getenv('PVE_PASSWORD')
        self.connections: Dict[str, ProxmoxAPI] = self._init_connections()

    def _is_connection_valid(self, conn):
        """检查连接是否有效"""
        try:
            # 执行简单的API调用验证连接
            conn.nodes.get()
            return True
        except Exception as e:
            self.logger.warning(f"PVE连接验证失败: {str(e)}")
            return False

    def _reconnect_node(self, node_name):
        """重新连接单个PVE节点"""
        try:
            self.logger.info(f"尝试重新连接PVE节点: {node_name}")
            conn = ProxmoxAPI(node_name, user=self.pve_user, password=self.pve_password, port=8006, verify_ssl=False)
            self.connections[node_name] = conn
            self.logger.info(f"PVE节点 {node_name} 重新连接成功")
            return True
        except Exception as e:
            self.logger.error(f"PVE节点 {node_name} 重新连接失败: {str(e)}")
            if node_name in self.connections:
                del self.connections[node_name]
            return False

    def _init_connections(self) -> Dict[str, ProxmoxAPI]:
        """初始化所有PVE节点的连接"""
        connections = {}
        for node in self.pve_nodes:
            try:
                conn: ProxmoxAPI = ProxmoxAPI(node, user=self.pve_user, password=self.pve_password, port=8006, verify_ssl=False)
                connections[node] = conn
            except Exception as e:
                import traceback
                print(f"连接PVE节点 {node} 失败: {str(e)}")
                traceback.print_exc()
        return connections

    def create_vm(self, node_name, vm_id, vm_name, cpu, memory, disk_size, gpu_pci_id):
        """创建带有GPU直通的虚拟机"""
        if node_name not in self.connections:
            return False, f"PVE节点 {node_name} 未连接"

        try:
            conn = self.connections[node_name]
            # 创建VM
            vm = conn.nodes(node_name).qemu.create(
                vmid=vm_id,
                name=vm_name,
                cores=cpu,
                memory=memory,
                net0='virtio,bridge=vmbr0',
                ide2='local:iso/ubuntu-22.04.iso,media=cdrom',
                scsi0='local-lvm:vm-{vm_id}-disk-0,size={disk_size}G'.format(vm_id=vm_id, disk_size=disk_size)
            )

            # 配置GPU直通
            conn.nodes(node_name).qemu(vm_id).config.set(
                hostpci0=f'{gpu_pci_id},pcie=1,x-vga=1'
            )

            # 启动VM
            conn.nodes(node_name).qemu(vm_id).status.start()
            return True, f"虚拟机 {vm_name} 创建成功"
        except Exception as e:
            return False, f"创建虚拟机失败: {str(e)}"

    def get_gpu_status(self, pve_name):
        """获取节点GPU使用情况（统计使用中的GPU数量）"""
        self.logger.info(f"开始获取节点 {pve_name} 的GPU状态")
        # 检查连接是否存在且有效
        if pve_name not in self.connections or not self._is_connection_valid(self.connections[pve_name]):
            self.logger.warning(f"PVE节点 {pve_name} 连接不存在或已失效")
            # 尝试重新连接
            if not self._reconnect_node(pve_name):
                self.logger.error(f"PVE节点 {pve_name} 重新连接失败")
                return False, f"PVE节点 {pve_name} 无法连接", 0

        try:
            conn = self.connections[pve_name]
            nodeStatus=[]
            # 获取所有虚拟机
            self.logger.info(f"成功连接到PVE节点 {pve_name}")
            nodes = conn.nodes.get()
            self.logger.info(f"获取到 {len(nodes)} 个节点信息")
            
            for node in nodes:
                node_name = node['node']
                self.logger.info(f"处理节点: {node_name}")
                nodeConn = conn.nodes(node_name)
                
                # 获取节点上的所有VM
                vms = nodeConn.qemu.get()
                self.logger.info(f"节点 {node_name} 上发现 {len(vms)} 个虚拟机")
                used_gpu_count = 0
                
                for vm in vms:
                    vm_used_gpu_count = 0
                    vmid = vm['vmid']
                    vm_name = vm['name']
                    self.logger.debug(f"检查虚拟机: {vmid} ({vm_name})")
                    
                    # 获取虚拟机状态
                    try:
                        status = nodeConn.qemu(vmid).status.current.get()
                        self.logger.debug(f"虚拟机 {vmid} 状态: {status['status']}")
                        
                        if status['status'] != 'running':
                            continue
                        
                        # 获取虚拟机配置
                        config = nodeConn.qemu(vmid).config.get()
                        pciList = []
                        vmStatus = {'vm_name': vm_name}
                        
                        for key, v in config.items():
                            if key.startswith('hostpci'):
                                pciList.append(v)
                                used_gpu_count += 1
                                vm_used_gpu_count += 1
                        
                        vmStatus['pci_list'] = pciList
                        vmStatus['vm_used_gpu_count'] = vm_used_gpu_count
                        
                        if pciList:
                            nodeStatus.append(vmStatus)
                            self.logger.info(f"虚拟机 {vmid} ({vm_name}) 使用 {vm_used_gpu_count} 个GPU: {pciList}")
                    except Exception as vm_e:
                        self.logger.error(f"处理虚拟机 {vmid} 时出错: {str(vm_e)}", exc_info=True)
                        continue
            
            self.logger.info(f"节点 {pve_name} GPU状态获取成功，共发现 {used_gpu_count} 个已使用GPU")
            return True, nodeStatus, used_gpu_count
        except Exception as e:
            self.logger.error(f"获取GPU状态失败: {str(e)}", exc_info=True)
            return False, f"获取GPU状态失败: {str(e)}", 0
