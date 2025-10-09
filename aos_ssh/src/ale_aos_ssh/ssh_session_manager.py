import datetime
import logging
import threading
import time
from threading import Lock

import paramiko

from .device_manager import Device, jump_ssh_boxes

logger = logging.getLogger("aos-ssh")

# Dictionary to store active SSH client sessions and their last activity time
# Key: IP Address (str)
# Value: {'client': paramiko.SSHClient, 'last_activity_time': datetime.datetime, 'lock': threading.Lock}
active_ssh_sessions = {}


# Define the inactivity timeout duration in seconds (5 minutes)
INACTIVITY_TIMEOUT = 5 * 60

# Uncomment for logging to a file
# from paramiko.util import log_to_file
# log_to_file(filename="paramiko.log", level=logging.DEBUG)


def create_ssh_session(
	host: str,
	username: str,
	password: str = None,
	key_filename: str = None,
	port: int = 22,
	jump_client: paramiko.SSHClient = None,
	jump_private_host: str = None,
	jump_private_port: int = 22,
):
	"""
	Creates and returns an SSH client session for the given host.
	Handles both password-based and key-based authentication.
	"""
	channel = None
	if jump_client is not None:
		logger.info(f"Creating SSH session to {host} via jump host")
		try:
			jump_transport = jump_client.get_transport()
			jump_transport.set_keepalive(15)
			jump_transport.use_compression(compress=False)
			dest_addr = (host, port)
			local_addr = (
				jump_private_host if jump_private_host is not None else jump_client.get_transport().getpeername()[0],
				jump_private_port,
			)
			# Local address can be arbitrary
			channel = jump_transport.open_channel("direct-tcpip", dest_addr, local_addr)
			channel.settimeout(60.0)
		except paramiko.ChannelException as e:
			return None, f"Failed to open channel through jump host: {e}"
		except paramiko.AuthenticationException:
			return None, f"Authentication failed for {username}@{host} via jump host"
		except paramiko.SSHException as e:
			return None, f"SSH error connecting to {host} via jump host: {e}"
		except OSError as e:
			return None, f"Network error connecting to {host} via jump host: {e}"
		except Exception as e:
			return None, f"An unexpected error occurred: {e}"

	client = paramiko.SSHClient()
	client.load_system_host_keys()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Be cautious with AutoAddPolicy in production

	try:
		if password:
			client.connect(hostname=host, port=port, username=username, password=password, timeout=10, sock=channel)
		elif key_filename:
			client.connect(hostname=host, port=port, username=key_filename, timeout=10, sock=channel)  # Corrected usage
		else:
			return None, f"No password or key_filename provided for {host}"
		transport = client.get_transport()
		transport.set_keepalive(60)
		logger.info(f"Successfully connected to {host}")
		return client, None
	except paramiko.AuthenticationException:
		return None, f"Authentication failed for {username}@{host}"
	except paramiko.SSHException as e:
		return None, f"SSH error connecting to {host}: {e}"
	except OSError as e:
		return None, f"Network error connecting to {host}: {e}"
	except Exception as e:
		return None, f"An unexpected error occurred: {e}"


def get_session(device: Device):
	"""Get or create an SSH session for the given device, handling jump hosts if necessary."""

	if device.jump_ssh_name is not None:
		jump_box = next((j for j in jump_ssh_boxes if j.name == device.jump_ssh_name), None)
		if jump_box is None:
			return None, f"Jump host {device.jump_ssh_name} not found for device {device.host}"
		logger.info(f"Using jump host {jump_box.name} ({jump_box.public_host}) to reach {device.host}")
		# First, get or create the jump box session
		jump_client, error_msg = get_or_create_session(
			host=jump_box.public_host,
			username=jump_box.user,
			password=jump_box.password,
			port=jump_box.public_port,
			is_jump_box=True,
			jump_name=jump_box.name,
		)

		if jump_client is None:
			return None, f"Failed to connect to jump host {jump_box.name}: {error_msg}"
		client, error_msg = get_or_create_session(
			host=device.host,
			port=device.port,
			username=device.user,
			password=device.password,
			is_jump_box=False,
			jump_name=jump_box.name,
			jump_client=jump_client,
			jump_private_host=jump_box.private_host,
			jump_private_port=jump_box.private_port,
		)
	else:
		client, error_msg = get_or_create_session(
			host=device.host, username=device.user, password=device.password, port=device.port
		)
	return client, error_msg


def get_or_create_session(
	host: str,
	username: str,
	password: str = "",
	key_filename: str = "",
	port: int = 22,
	is_jump_box: bool = False,
	jump_name: str = "",
	jump_client: paramiko.SSHClient = None,
	jump_private_host: str = "",
	jump_private_port: int = 22,
):
	"""
	Retrieves an existing active session or creates a new one if it doesn't exist or is closed.
	Updates the last_activity_time for the session.
	"""
	logger.info(f"Checking session for {host} {username} , port {port}")
	# The dictionary itself needs a small lock just for adding/removing keys
	# But access to the *values* (the sessions) will be managed by their own locks
	# We can use a simple global lock here since it's a very fast operation
	# that doesn't involve waiting for network I/O
	# Use host:port as key for jump boxes to allow multiple jump boxes to same host on different ports
	if (host, is_jump_box, jump_name) not in active_ssh_sessions:
		active_ssh_sessions[(host, is_jump_box, jump_name)] = {"lock": Lock()}  # Add lock for this host first

	session_info = active_ssh_sessions[(host, is_jump_box, jump_name)]
	with session_info["lock"]:  # Acquire the lock for this specific session
		client = session_info.get("client")  # Use .get() to handle case where client isn't set yet

		# Check if the existing client is still active
		if client:
			try:
				transport = client.get_transport()
				if transport and transport.is_active() and transport.send_ignore():
					logger.info(f"Using existing active session for {host}")
					# Update activity time since session is being accessed
					session_info["last_activity_time"] = datetime.datetime.now()
					return client, None
				else:
					logger.info(f"Session for {host} found but is not active. Reconnecting...")
					client.close()  # Ensure old transport is closed
					client, error_msg = create_ssh_session(
						host, username, password, key_filename, port, jump_client, jump_private_host, jump_private_port
					)
					if client:
						session_info["client"] = client
						session_info["is_jump_box"] = is_jump_box
						session_info["jump_name"] = jump_name
						session_info["jump_client"] = jump_client
						session_info["last_activity_time"] = datetime.datetime.now()
					return client, error_msg
			except EOFError:
				logger.info(f"Session for {host} unexpectedly closed. Reconnecting...")
				client.close()
				client, error_msg = create_ssh_session(
					host, username, password, key_filename, port, jump_client, jump_private_host, jump_private_port
				)
				if client:
					session_info["client"] = client
					session_info["is_jump_box"] = is_jump_box
					session_info["jump_name"] = jump_name
					session_info["jump_client"] = jump_client
					session_info["last_activity_time"] = datetime.datetime.now()
				return client, error_msg
			except Exception as e:
				logger.info(f"Error checking session for {host}: {e}. Reconnecting...")
				if client:
					client.close()
				client, error_msg = create_ssh_session(
					host, username, password, key_filename, port, jump_client, jump_private_host, jump_private_port
				)
				if client:
					session_info["client"] = client
					session_info["is_jump_box"] = is_jump_box
					session_info["jump_name"] = jump_name
					session_info["jump_client"] = jump_client
					session_info["last_activity_time"] = datetime.datetime.now()
				return client, error_msg
		else:
			logger.info(f"No existing session for {host}. Creating a new one...")
			client, error_msg = create_ssh_session(
				host, username, password, key_filename, port, jump_client, jump_private_host, jump_private_port
			)
			logger.info(f"create_ssh_session result for {host} , error : {error_msg}")
			if client:
				session_info["client"] = client
				session_info["is_jump_box"] = is_jump_box
				session_info["jump_name"] = jump_name
				session_info["jump_client"] = jump_client
				session_info["last_activity_time"] = datetime.datetime.now()
			return client, error_msg


def execute_command(host, command, jump_name=None):
	"""
	Executes a command on the specified SSH session.
	Assumes the session is already managed by get_or_create_session.
	Updates the last_activity_time for the session.
	"""

	if (host, False, jump_name) not in active_ssh_sessions:
		print(f"No active session for {host}. Please establish a connection first.")
		return None, None, None

	session_info = active_ssh_sessions[(host, False, jump_name)]
	with session_info["lock"]:  # Acquire the lock for this specific session
		client = session_info.get("client")
		if not client:
			logger.info(f"No active client found within the session info for {host}.")
			return None, None, None

		try:
			stdin, stdout, stderr = client.exec_command(command)
			output = stdout.read().decode().strip()
			error = stderr.read().decode().strip()

			# Update activity time after successful command execution
			session_info["last_activity_time"] = datetime.datetime.now()

			return stdin, output, error
		except paramiko.SSHException as e:
			logger.info(f"Error executing command on {host}: {e}")
			return None, None, str(e)
		except Exception as e:
			logger.info(f"An unexpected error occurred while executing command: {e}")
			return None, None, str(e)


def close_session(host, is_jump_box, jump_name):
	"""Closes a specific SSH session and removes it from the map."""
	session_info = active_ssh_sessions.get((host, is_jump_box, jump_name))
	if session_info:
		with session_info["lock"]:
			client = session_info.get("client")
			if client:
				try:
					client.close()
					logger.info(f"Closed session for {host} due to inactivity or explicit call.")
				except Exception as e:
					logger.info(f"Error closing session for {host}: {e}")
		# Remove the entry from the global dict *after* releasing the per-session lock
		if (host, is_jump_box, jump_name) in active_ssh_sessions:
			del active_ssh_sessions[(host, is_jump_box, jump_name)]


def close_all_sessions():
	"""Closes all active SSH sessions."""
	# Create a list of IPs to avoid RuntimeError due to dictionary size change during iteration
	hosts_to_close = list(active_ssh_sessions.keys())
	for host, is_jump_box, jump_name in hosts_to_close:
		close_session(host, is_jump_box, jump_name)


def inactivity_cleanup_thread(interval=30):
	"""
	A separate thread to periodically check for and close inactive SSH sessions.
	"""
	while True:
		current_time = datetime.datetime.now()
		hosts_to_close = []
		jump_ssh_boxes_counter: dict[str, int] = {}

		# Iterate over a copy of keys to safely handle deletions
		for host, is_jump_box, jump_name in list(active_ssh_sessions.keys()):
			session_info = active_ssh_sessions.get((host, is_jump_box, jump_name))
			if session_info and "lock" in session_info:
				# Use a non-blocking lock acquire (try_acquire) to avoid holding up the cleanup
				# if another thread has a long-running operation on a session
				if session_info["lock"].acquire(blocking=False):
					try:
						is_jump_box_: bool = session_info.get("is_jump_box")
						jump_name_: str = session_info.get("jump_name")
						if jump_name_ and not is_jump_box_:
							jump_ssh_boxes_counter[jump_name_] = jump_ssh_boxes_counter.get(jump_name_, 0) + 1
						last_activity = session_info.get("last_activity_time")
						if (
							not is_jump_box_
							and last_activity
							and (current_time - last_activity).total_seconds() > INACTIVITY_TIMEOUT
						):
							hosts_to_close.append((host, is_jump_box_, jump_name_))
					finally:
						session_info["lock"].release()

		for host, is_jump_box, jump_name in hosts_to_close:
			logger.info(f"Session for {host} has been inactive for more than {INACTIVITY_TIMEOUT} seconds. Closing...")
			close_session(host, is_jump_box, jump_name)

		# Now check jump boxes to see if they can be closed (no active sessions using them)
		for jump_box in jump_ssh_boxes:
			if jump_box.name not in jump_ssh_boxes_counter:
				host = jump_box.public_host
				session_info = active_ssh_sessions.get((host, True, jump_box.name))
				if session_info:
					close_session(host, True, jump_box.name)

		time.sleep(interval)


def init_ssh_session_manager():
	"""
	Initializes the SSH session manager.
	This can be called at the start of your application to set up the cleanup thread.
	"""
	cleanup_thread = threading.Thread(target=inactivity_cleanup_thread, daemon=True)
	cleanup_thread.start()
	logger.info(f"Inactivity cleanup thread started with a timeout of {INACTIVITY_TIMEOUT} seconds.")


# --- Example Usage ---
if __name__ == "__main__":
	# IMPORTANT: Replace these with your actual server details
	# For testing, you can use a local Vagrant/Docker SSH server or a cloud VM

	# Example 1: Using password authentication
	# server_ip_1 = "your_server_ip_1"
	# ssh_username_1 = "your_username_1"
	# ssh_password_1 = "your_password_1"

	# Example 2: Using key-based authentication
	# server_ip_2 = "your_server_ip_2"
	# ssh_username_2 = "your_username_2"
	# ssh_key_path_2 = "/path/to/your/private_key.pem" # e.g., ~/.ssh/id_rsa

	# Start the inactivity cleanup thread
	cleanup_thread = threading.Thread(target=inactivity_cleanup_thread, daemon=True)
	cleanup_thread.start()
	print(f"Inactivity cleanup thread started with a timeout of {INACTIVITY_TIMEOUT} seconds.")

	# Placeholder for actual usage, demonstrating the structure
	# Uncomment and fill in details to run

	# print("--- Attempting to connect to server 1 (password) ---")
	# client1 = get_or_create_session(server_ip_1, ssh_username_1, password=ssh_password_1)
	# if client1:
	#     print(f"Session for {server_ip_1} is active.")
	#     stdin, stdout, stderr = execute_command(server_ip_1, "ls -l")
	#     if stdout:
	#         print(f"Command output for {server_ip_1}:\n{stdout}")
	#     if stderr:
	#         print(f"Command error for {server_ip_1}:\n{stderr}")
	# else:
	#     print(f"Failed to establish session for {server_ip_1}")

	# print("\n--- Attempting to connect to server 2 (key-based) ---")
	# client2 = get_or_create_session(server_ip_2, ssh_username_2, key_filename=ssh_key_path_2)
	# if client2:
	#     print(f"Session for {server_ip_2} is active.")
	#     stdin, stdout, stderr = execute_command(server_ip_2, "hostname")
	#     if stdout:
	#         print(f"Command output for {server_ip_2}:\n{stdout}")
	#     if stderr:
	#         print(f"Command error for {server_ip_2}:\n{stderr}")
	# else:
	#     print(f"Failed to establish session for {server_ip_2}")

	# print("\n--- Demonstrating session reuse ---")
	# client1_again = get_or_create_session(server_ip_1, ssh_username_1, password=ssh_password_1)
	# if client1_again == client1:
	#     print(f"Session for {server_ip_1} was reused successfully.")

	# print("\n--- Starting a session monitor thread for server 1 (if active keep-alive is desired) ---")
	# # This thread will run in the background, keeping the session alive even with no commands
	# # monitor_thread_1 = threading.Thread(target=session_monitor_thread,
	# #                                       args=(server_ip_1, ssh_username_1, ssh_password_1), daemon=True)
	# # monitor_thread_1.start()

	# # Keep the main thread alive for a bit to allow the monitor and cleanup threads to run
	# # You can test inactivity by making initial connections, then waiting longer than INACTIVITY_TIMEOUT
	# # time.sleep(360) # Wait for 6 minutes (longer than 5 min timeout) to observe cleanup

	print("\n--- To observe inactivity timeout, make connections and then wait ---")
	print("For example, uncomment and run the connection blocks, then wait for >5 minutes.")
	print("Manual cleanup is still available: close_all_sessions()")

	# When the main program finishes, daemon threads will automatically terminate
	# For a long-running application, you might have a main loop here.
	# For this example, we'll just demonstrate the immediate functionality.
	# If you remove the time.sleep(360) above, the script will exit quickly.
