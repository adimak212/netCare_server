from __future__ import annotations

from typing import Optional, Dict
import logging

from pysnmp.hlapi.v1arch import (
    SnmpDispatcher,
    CommunityData,
    UdpTransportTarget,
    ObjectType,
    ObjectIdentity,
    get_cmd,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("snmp")

OIDS = {
    "sysDescr": "1.3.6.1.2.1.1.1.0",
    "sysName": "1.3.6.1.2.1.1.5.0",
    "sysObjectID": "1.3.6.1.2.1.1.2.0",
}

def snmp_get(ip: str, oid: str, community: str = "public", timeout: int = 2, retries: int = 1) -> Optional[str]:
    try:
        it = get_cmd(
            SnmpDispatcher(),
            CommunityData(community),
            UdpTransportTarget((ip, 161), timeout=timeout, retries=retries),
            ObjectType(ObjectIdentity(oid)),
        )

        error_indication, error_status, error_index, var_binds = next(it)

        if error_indication:
            logger.debug(f"{ip} errorIndication={error_indication}")
            return None

        if error_status:
            logger.debug(f"{ip} errorStatus={error_status.prettyPrint()}")
            return None

        for vb in var_binds:
            return str(vb[1])

        return None
    except Exception as e:
        logger.debug(f"{ip} exception={e}")
        return None

def snmp_basic_info(ip: str, community: str = "public", timeout: int = 2, retries: int = 1) -> Optional[Dict[str, str]]:
    sys_descr = snmp_get(ip, OIDS["sysDescr"], community, timeout, retries)
    if not sys_descr:
        return None

    sys_name = snmp_get(ip, OIDS["sysName"], community, timeout, retries)
    sys_object_id = snmp_get(ip, OIDS["sysObjectID"], community, timeout, retries)

    return {
        "sysDescr": sys_descr,
        "sysName": sys_name or "",
        "sysObjectID": sys_object_id or "",
    }
