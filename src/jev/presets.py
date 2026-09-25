"""Pre-built evaluation presets showcasing Choice, Score, and Noul primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from jev.models import ChoiceQuestion, NoulQuestion, Question, ScoreQuestion


@dataclass
class Preset:
    id: str
    title: str
    description: str
    state: Any
    questions: Dict[str, Question]


PRESETS: List[Preset] = [
    Preset(
        id="ot_hmi_normal",
        title="OT 產線：正常運行的 HMI 設備",
        description="分析人機介面 (HMI) 之運作程序與 PLC 協定連線，判斷設備角色與安全狀態。",
        state={
            "running_processes": [
                "CimView.exe",
                "IntelGraphics.exe",
                "hmi_runtime.exe",
            ],
            "network_connections": {
                "inbound": [],
                "outbound": [
                    "192.168.10.5:502 (Modbus/TCP)",
                    "192.168.10.10:44818 (EtherNet/IP)",
                ],
            },
        },
        questions={
            "asset_classification": ChoiceQuestion(
                instructions="根據這台機器的執行程序與網路連線特徵，它最符合哪一種 OT 設備角色？",
                criteria={
                    "MES": "製造執行系統。特徵為含有 ERP 串接、資料庫連線、特定生產看板程序，且通常位於 Purdue Model 的 Level 3。",
                    "SCADA": "監控與資料擷取伺服器。特徵為同時有大量的 PLC 協定連線（如 Modbus, S7），並與多個 HMI 連線，通常有歷史資料庫（Historian）程序。",
                    "HMI": "人機介面觸控螢幕。特徵為通常運行特定廠商的 runtime 面板軟體，連線相對單純（通常只對應特定 1-2 台 PLC 或 SCADA 伺服器）。",
                    "Engineering_Station": "工程師工作站。特徵為擁有 PLC 梯形圖編寫軟體（如 TIA Portal, Studio 5000），且連線行為不規律，常有對 PLC 的 80/4433 部署行為。",
                },
            ),
            "anomaly_detected": NoulQuestion(
                instructions="檢視該機器的運行程序與網路連線，是否存在「不符合該 OT 角色常態」的異常行為（如：非工業協定外網連線、未授權的 IT/管理工具、非典型跨區連線）？",
                criteria={
                    "true": "存在異常行為（如非工業外網連線、未授權遠端/管理工具、非典型跨區連線）",
                    "false": "所有執行程序與網路連線皆符合該 OT 設備角色常態與基線規範",
                },
            ),
            "threat_severity": ScoreQuestion(
                instructions="評估該設備當前的異常威脅與風險等級 (Threat Severity Level)。",
                criteria=[
                    "Level 1: 正常運行，無可疑程序或連線",
                    "Level 2: 輕微或非典型行為，需進一步排查確認",
                    "Level 3: 嚴重異常或遭入侵指標 (IOC)，需立即隔離切斷",
                ],
            ),
        },
    ),
    Preset(
        id="ot_mes_normal",
        title="OT 產線：正常運行的 MES 伺服器",
        description="分析製造執行系統 (MES) 之資料庫、ERP 串接與 MQTT 連線特徵。",
        state={
            "running_processes": [
                "MesCoreService.exe",
                "sqlservr.exe",
                "RabbitMQ.exe",
                "Tomcat9.exe",
            ],
            "network_connections": {
                "inbound": [
                    "*:8080 (HTTP 看板服務)",
                    "*:1433 (MSSQL)",
                ],
                "outbound": [
                    "10.0.1.50:443 (連往 IT 區 ERP 伺服器)",
                    "192.168.10.2:1883 (MQTT 連往 SCADA)",
                ],
            },
        },
        questions={
            "asset_classification": ChoiceQuestion(
                instructions="根據這台機器的執行程序與網路連線特徵，它最符合哪一種 OT 設備角色？",
                criteria={
                    "MES": "製造執行系統。特徵為含有 ERP 串接、資料庫連線、特定生產看板程序，且通常位於 Purdue Model 的 Level 3。",
                    "SCADA": "監控與資料擷取伺服器。特徵為同時有大量的 PLC 協定連線（如 Modbus, S7），並與多個 HMI 連線，通常有歷史資料庫（Historian）程序。",
                    "HMI": "人機介面觸控螢幕。特徵為通常運行特定廠商的 runtime 面板軟體，連線相對單純（通常只對應特定 1-2 台 PLC 或 SCADA 伺服器）。",
                    "Engineering_Station": "工程師工作站。特徵為擁有 PLC 梯形圖編寫軟體（如 TIA Portal, Studio 5000），且連線行為不規律，常有對 PLC 的 80/4433 部署行為。",
                },
            ),
            "anomaly_detected": NoulQuestion(
                instructions="檢視該機器的運行程序與網路連線，是否存在「不符合該 OT 角色常態」的異常行為（如：非工業協定外網連線、未授權的 IT/管理工具、非典型跨區連線）？",
                criteria={
                    "true": "存在異常行為（如非工業外網連線、未授權遠端/管理工具、非典型跨區連線）",
                    "false": "所有執行程序與網路連線皆符合該 OT 設備角色常態與基線規範",
                },
            ),
            "threat_severity": ScoreQuestion(
                instructions="評估該設備當前的異常威脅與風險等級 (Threat Severity Level)。",
                criteria=[
                    "Level 1: 正常運行，無可疑程序或連線",
                    "Level 2: 輕微或非典型行為，需進一步排查確認",
                    "Level 3: 嚴重異常或遭入侵指標 (IOC)，需立即隔離切斷",
                ],
            ),
        },
    ),
    Preset(
        id="ot_scada_compromised",
        title="OT 產線：疑似遭到入侵的 SCADA 伺服器",
        description="檢視出現 PowerShell、AnyDesk 及不明外網連線之 SCADA 伺服器，評估入侵指標與風險。",
        state={
            "running_processes": [
                "Siemens.WinCC.exe",
                "CcHistorian.exe",
                "powershell.exe",
                "anydesk.exe",
            ],
            "network_connections": {
                "inbound": [
                    "*:102 (S7 Comm)",
                    "*:4840 (OPC UA)",
                ],
                "outbound": [
                    "192.168.10.25:445 (SMB 跨區連線)",
                    "45.123.8.9:443 (外部不明 IP)",
                ],
            },
        },
        questions={
            "asset_classification": ChoiceQuestion(
                instructions="根據這台機器的執行程序與網路連線特徵，它最符合哪一種 OT 設備角色？",
                criteria={
                    "MES": "製造執行系統。特徵為含有 ERP 串接、資料庫連線、特定生產看板程序，且通常位於 Purdue Model 的 Level 3。",
                    "SCADA": "監控與資料擷取伺服器。特徵為同時有大量的 PLC 協定連線（如 Modbus, S7），並與多個 HMI 連線，通常有歷史資料庫（Historian）程序。",
                    "HMI": "人機介面觸控螢幕。特徵為通常運行特定廠商的 runtime 面板軟體，連線相對單純（通常只對應特定 1-2 台 PLC 或 SCADA 伺服器）。",
                    "Engineering_Station": "工程師工作站。特徵為擁有 PLC 梯形圖編寫軟體（如 TIA Portal, Studio 5000），且連線行為不規律，常有對 PLC 的 80/4433 部署行為。",
                },
            ),
            "anomaly_detected": NoulQuestion(
                instructions="檢視該機器的運行程序與網路連線，是否存在「不符合該 OT 角色常態」的異常行為（如：非工業協定外網連線、未授權的 IT/管理工具、非典型跨區連線）？",
                criteria={
                    "true": "存在異常行為（如非工業外網連線、未授權遠端/管理工具、非典型跨區連線）",
                    "false": "所有執行程序與網路連線皆符合該 OT 設備角色常態與基線規範",
                },
            ),
            "threat_severity": ScoreQuestion(
                instructions="評估該設備當前的異常威脅與風險等級 (Threat Severity Level)。",
                criteria=[
                    "Level 1: 正常運行，無可疑程序或連線",
                    "Level 2: 輕微或非典型行為，需進一步排查確認",
                    "Level 3: 嚴重異常或遭入侵指標 (IOC)，需立即隔離切斷",
                ],
            ),
        },
    ),
]


def get_preset_by_id(preset_id: str) -> Preset:
    for p in PRESETS:
        if p.id == preset_id:
            return p
    raise ValueError(f"Unknown preset id: {preset_id}")
