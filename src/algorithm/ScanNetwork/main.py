# בתוך main.py
from .netCareScanner import NetCareScanner
import asyncio

async def main():
    network_input = input("Enter Network (e.g. 10.10.10.0/24): ")
    first_ip = input("Enter first device IP to scan: ")
    user = "admin"
    pwd = "1234"

    scanner = NetCareScanner(user, pwd, network_input)
    await scanner.scan_device(first_ip, "Core-Router")
    scanner.save_to_json()

if __name__ == "__main__":
    asyncio.run(main())