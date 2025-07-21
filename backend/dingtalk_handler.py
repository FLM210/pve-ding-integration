# !/usr/bin/env python
import logging,os
from dingtalk_stream import AckMessage
import dingtalk_stream
from pve_manager import PVEManager
def setup_logger():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter('%(asctime)s %(name)-8s %(levelname)-8s %(message)s [%(filename)s:%(lineno)d]'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
pve = PVEManager()
class CalcBotHandler(dingtalk_stream.ChatbotHandler):
    def __init__(self, logger: logging.Logger = None):
        super(dingtalk_stream.ChatbotHandler, self).__init__()
        if logger:
            self.logger = logger

    async def process(self, callback: dingtalk_stream.CallbackMessage):
        incoming_message = dingtalk_stream.ChatbotMessage.from_dict(callback.data)
        expression = incoming_message.text.content.strip()
        # try:
        #     result = eval(expression)
        # except Exception as e:
        #     result = 'Error: %s' % e
        # self.logger.info('%s = %s' % (expression, result))
        self.logger.info(f'收到消息：{expression}')
        match expression:
            case "":
                all_status={}
                for pve_node in pve.pve_nodes:
                    ok, result,_ = pve.get_gpu_status(pve_node)
                    if ok:
                        all_status[pve_node] = result
                    else:
                        self.reply_text(result,incoming_message)
                        return AckMessage.STATUS_OK, 'OK'
                self.reply_text(generate_dingtalk_gpu_message(all_status),incoming_message)
                return AckMessage.STATUS_OK, 'OK'
            case expression if expression in pve.pve_nodes:
                ok, result,_ = pve.get_vm_status(expression)
                if ok:
                    self.reply_text(generate_message_about_single_server(result),incoming_message)
                else:
                    self.reply_text(result,incoming_message)
                return AckMessage.STATUS_OK, 'OK'
            case "help":   
                self.reply_text("""支持命令：
1. 空消息：获取所有服务器GPU使用情况
2. 服务器IP：获取指定服务器所有虚拟机信息
3. help：获取帮助信息
其他功能开发中🌀🌀🌀
""",incoming_message)
                return AckMessage.STATUS_OK, 'OK'

def run_robot():
    logger = setup_logger()
    env=os.getenv('ENV')
    credential = dingtalk_stream.Credential(os.getenv(env+'_DINGTALK_APP_KEY'), os.getenv(env+'_DINGTALK_APP_SECRET'))
    # credential = dingtalk_stream.Credential(os.getenv('DGENE_DINGTALK_APP_KEY'), os.getenv('DGENE_DINGTALK_APP_SECRET'))
    client = dingtalk_stream.DingTalkStreamClient(credential)
    client.register_callback_handler(dingtalk_stream.chatbot.ChatbotMessage.TOPIC, CalcBotHandler(logger))
    client.start_forever()




def generate_dingtalk_gpu_message(data, total_gpus_per_node=4):
    """
    生成适合钉钉移动客户端的GPU使用情况报告
    
    Args:
        data: 接口返回的GPU使用数据（字典格式）
        total_gpus_per_node: 每台服务器的总GPU数量，默认为8
    
    Returns:
        str: 优化移动端显示的纯文本消息
    """
    # 定义分隔符（缩短长度适应手机屏幕）
    TITLE_SEP = "=" * 16
    SECTION_SEP = "-" * 20
    ITEM_SEP = "·" * 20
    
    # 初始化消息内容
    message = f"📊 {TITLE_SEP} 📊\n"
    message += "   GPU资源使用报告\n"
    message += f"📊 {TITLE_SEP} 📊\n\n"
    
    # 遍历每个服务器节点
    for node_ip, vms in data.items():
        ip = node_ip.split(':')[0]
        used = sum(vm["vm_used_gpu_count"] for vm in vms)
        free = max(0, total_gpus_per_node - used)
        usage = (used / total_gpus_per_node) * 100
        
        # 负载状态图标
        status = "🔴🔥" if usage >= 80 else "🟡⚠️" if usage >= 50 else "🟢✅"
        
        message += f"🖥️【{ip}】{status}\n"
        message += f"{ITEM_SEP}\n"
        message += f"  🟢 已用: {used}/{total_gpus_per_node}张\n"
        message += f"  🟡 剩余: {free}张\n"
        message += f"  📈 使用率: {usage:.1f}%\n\n"
        
        # 虚拟机详情
        message += "  🖥️ 虚拟机分配:\n"
        for vm in vms:
            name = vm["vm_name"]
            gpu = vm["vm_used_gpu_count"]
            pci = ", ".join([pci.split(',')[0] for pci in vm["pci_list"]])
            message += f"  • {name}: {gpu}张 ({pci})\n"
        message += f"{SECTION_SEP}\n\n"
    
    # 全局统计
    total_nodes = len(data)
    total_used = sum(sum(vm["vm_used_gpu_count"] for vm in vms) for vms in data.values())
    total_free = total_nodes * total_gpus_per_node - total_used
    overall_usage = (total_used / (total_nodes * total_gpus_per_node)) * 100
    
    message += f"📊 {TITLE_SEP} 📊\n"
    message += "    集群整体统计\n"
    message += f"📊 {TITLE_SEP} 📊\n"
    message += f"🖥️ 服务器: {total_nodes}台\n"
    message += f"🔧 已用GPU: {total_used}张\n"
    message += f"💡 剩余GPU: {total_free}张\n"
    message += f"📈 GPU总使用率: {overall_usage:.1f}%\n"
    message += f"{TITLE_SEP}\n"
    message += f"⚙️ 发送help获取更多使用介绍"
    
    return message
if __name__ == '__main__':
    run_robot()