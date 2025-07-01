import urllib3,threading
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from uvicorn import Server
from uvicorn.config import Config
from dotenv import load_dotenv
from pve_manager import PVEManager
from dingtalk_handler import run_robot
# 加载环境变量
load_dotenv()

app = FastAPI(title="PVE-DingTalk Integration API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "PVE-DingTalk Integration API is running"}

@app.post("/dingtalk/callback")
async def dingtalk_callback(request: Request):
    timestamp = request.headers.get("timestamp")
    nonce = request.headers.get("nonce")
    signature = request.headers.get("signature")
    body = await request.body()
    encrypt_msg = body.decode()

    dingtalk = DingTalkHandler()
    if not dingtalk.verify_callback(timestamp, nonce, signature, encrypt_msg):
        raise HTTPException(status_code=403, detail="签名验证失败")

    data = json.loads(encrypt_msg)
    event_type = data.get("EventType")
    if event_type == "bpms_instance_change":
        success, result = dingtalk.process_approval_event(data.get("processInstance"))
        if success and result["status"] == "COMPLETED":
            pve = PVEManager()
            form_data = result["form_data"]
            # 创建虚拟机
            vm_success, vm_msg = pve.create_vm(
                node_name=form_data["PVE节点"],
                vm_id=int(form_data["虚拟机ID"]),
                vm_name=form_data["虚拟机名称"],
                cpu=int(form_data["CPU核心数"]),
                memory=int(form_data["内存大小(MB)"]),
                disk_size=int(form_data["磁盘大小(GB)"]),
                gpu_pci_id=form_data["GPU PCIe ID"]
            )
            # 发送通知
            dingtalk.send_robot_message(f"虚拟机创建{vm_success and '成功' or '失败'}: {vm_msg}")
            return {"status": "success", "message": vm_msg}
    return {"status": "success"}

@app.get("/gpu/status")
def get_gpu_status(node_name: str = None):
    pve = PVEManager()
    if node_name:
        success, result = pve.get_gpu_status(node_name)
        return {"node": node_name, "success": success, "data": result}
    else:
        # 获取所有节点GPU状态
        all_status = {}
        for pve_node in pve.pve_nodes:
            success, result,_ = pve.get_gpu_status(pve_node)
            # all_status[pve_node] = {"success": success, "data": result}
            all_status[pve_node] = result
        return all_status


async def run_fastapi():
    config = Config(app=app, host="0.0.0.0", port=8000)
    server = Server(config)
    await server.serve()
def start_fastapi():
    import asyncio
    asyncio.run(run_fastapi())

if __name__ == "__main__":
    # 启动FastAPI服务线程
    fastapi_thread = threading.Thread(target=start_fastapi)
    fastapi_thread.daemon = True
    fastapi_thread.start()

    # 启动钉钉机器人线程
    robot_thread = threading.Thread(target=run_robot)
    robot_thread.daemon = True
    robot_thread.start()
    try:
        from threading import Event
        Event().wait()
    except KeyboardInterrupt:
        print("程序已停止")