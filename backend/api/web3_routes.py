import sys
import os

from fastapi import APIRouter

# 加入 web3 模組路徑
WEB3_DIR = "/Users/aitree414/Documents/investment"
if WEB3_DIR not in sys.path:
    sys.path.insert(0, WEB3_DIR)

router = APIRouter()


@router.get("/web3/gas")
def get_gas():
    """取得當前 Gas 費用"""
    try:
        from web3.gas_tracker import get_ethereum_gas
        data = get_ethereum_gas()
        if not data:
            return {"error": "無法取得 Gas 數據"}
        slow = data["slow"]
        if slow < 10:
            status = "極低"
            color = "success"
        elif slow < 20:
            status = "偏低"
            color = "success"
        elif slow < 50:
            status = "正常"
            color = "warning"
        else:
            status = "偏高"
            color = "danger"
        return {**data, "status": status, "color": color}
    except Exception as e:
        return {"error": str(e)}


@router.get("/web3/defi")
def get_defi():
    """取得 DeFi 最高收益池"""
    try:
        from web3.defi_monitor import DeFiMonitor
        monitor = DeFiMonitor()
        pools = monitor.get_top_yields()
        return {"pools": pools[:8]}
    except Exception as e:
        return {"error": str(e), "pools": []}


@router.get("/web3/airdrops")
def get_airdrops():
    """取得 Airdrop 任務清單"""
    try:
        from web3.airdrop_tracker import AirdropTracker
        tracker = AirdropTracker()
        projects = tracker.projects.get("projects", [])
        return {"projects": projects}
    except Exception as e:
        return {"error": str(e), "projects": []}
