import os
from proxmoxer import ProxmoxAPI
from typing import Dict, Optional
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

class PVEManager:
    def __init__(self):
        self.pve_nodes = os.getenv('PVE_NODES', 'pve1,pve2,pve3,pve4').split(',')
        self.pve_user = os.getenv('PVE_USER')
        self.pve_password = os.getenv('PVE_PASSWORD')
        self.connections: Dict[str, ProxmoxAPI] = self._init_connections()

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
        if pve_name not in self.connections:
            return False, f"PVE节点 {pve_name} 未连接"

        try:
            conn = self.connections[pve_name]
            nodeStatus=[]
            # 获取所有虚拟机
            for node in conn.nodes.get():
                node_name = node['node']
                nodeConn=conn.nodes(node_name)
                vms = nodeConn.qemu.get()
                used_gpu_count = 0
                pciList=nodeConn.hardware.pci.get()
                for vm in vms:
                    vm_used_gpu_count = 0
                    vmid = vm['vmid']
                    # 获取虚拟机状态
                    status = nodeConn.qemu(vmid).status.current.get()
                    if status['status'] != 'running':
                        continue
                    #  conn.nodes(node_name).pci
                    # 获取虚拟机配置
                    config = nodeConn.qemu(vmid).config.get()
                    # 检查是否有PCI直通设备（GPU）
                    pciList=[]
                    vmStatus={}
                    for key, v in config.items():
                        if key.startswith('hostpci'): 
                            pciList.append(v)
                            used_gpu_count += 1
                            vm_used_gpu_count += 1
                    vmStatus['vm_name']=vm['name']
                    vmStatus['pci_list']=pciList
                    vmStatus['vm_used_gpu_count']=vm_used_gpu_count
                    if len(pciList) != 0:
                        nodeStatus.append(vmStatus)
                
            return True, nodeStatus,used_gpu_count
        except Exception as e:
            return False, f"获取GPU状态失败: {str(e)}"
