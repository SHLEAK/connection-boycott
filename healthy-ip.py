import subprocess
import time
import ipaddress
import signal
import sys

FILE_PATH = "~/us-aggregated.zone.txt"#example, download and replace name
#https://www.ipdeny.com/ipblocks/data/aggregated/us-aggregated.zone
#download from here
running = True
#this code has not been tested for windows, but probably won't work as it uses linux commands


# --- handle CTRL+C cleanly ---
def handle_exit(sig, frame):
	global running
	print("\n[+] stopping monitor...")
	running = False


signal.signal(signal.SIGINT, handle_exit)


# --- load IP ranges once ---
def load_ranges(path):
	nets = []
	with open(path, "r") as f:
		for line in f:
			line = line.strip()
			if not line:
				continue
			try:
				nets.append(ipaddress.ip_network(line))
			except:
				pass
	return nets


BLOCKED_RANGES = load_ranges(FILE_PATH)

# --- fast check ---
def ip_is_blocked(ip):
	try:
		ip_obj = ipaddress.ip_address(ip)
		return any(ip_obj in net for net in BLOCKED_RANGES)
	except:
		return False


# --- get live connections ---
def get_connections():
	result = subprocess.run(
		["lsof", "-i", "-n", "-P"],
		capture_output=True,
		text=True
	)

	lines = result.stdout.splitlines()[1:]
	conns = []

	for line in lines:
		parts = line.split()

		if len(parts) < 9:
			continue

		try:
			pid = int(parts[1])
			name = parts[0]
			addr = parts[-1]

			if "->" in addr:
				remote = addr.split("->")[-1]
				ip = remote.split(":")[0]
				conns.append((pid, name, ip))

		except:
			continue

	return conns


def kill(pid, name, ip):
	print(f"[kill] {name} (pid {pid}) -> {ip}")
	subprocess.run(
		["kill", "-9", str(pid)],
		stdout=subprocess.DEVNULL,
		stderr=subprocess.DEVNULL
	)

def monitor():
	print("[+] monitoring processes using ip blocklist...")
	print(f"[+] loaded {len(BLOCKED_RANGES)} ip ranges")
	print("[+] press ctrl+c to stop")

	while running:
		conns = get_connections()

		for pid, name, ip in conns:
			if ip_is_blocked(ip):
				kill(pid, name, ip)

		time.sleep(1)

	print("[+] monitor stopped")
	sys.exit(0)


if __name__ == "__main__":
	monitor()
