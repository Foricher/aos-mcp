import paramiko
import time
import socket
import threading
import datetime

# Dictionary to store active SSH client sessions and their last activity time
# Key: IP Address (str)
# Value: {'client': paramiko.SSHClient, 'last_activity_time': datetime.datetime}
active_ssh_sessions = {}
# A lock to protect access to the active_ssh_sessions dictionary
session_lock = threading.Lock()

# Define the inactivity timeout duration in seconds (5 minutes)
INACTIVITY_TIMEOUT = 5 * 60

def create_ssh_session(host, username, password=None, key_filename=None, port=22):
    """
    Creates and returns an SSH client session for the given host.
    Handles both password-based and key-based authentication.
    """
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Be cautious with AutoAddPolicy in production
    
    try:
        if password:
            client.connect(hostname=host, port=port, username=username, password=password, timeout=10)
        elif key_filename:
            client.connect(hostname=host, port=port, username=username, key_filename=key_filename, timeout=10)
        else:
            return None, f"No password or key_filename provided for {host}"
        transport = client.get_transport()
        transport.set_keepalive(60)
        print(f"Successfully connected to {host}")
        return client, None
    except paramiko.AuthenticationException:
        return None, f"Authentication failed for {username}@{host}"
    except paramiko.SSHException as e:
        return None, f"SSH error connecting to {host}: {e}"
    except socket.error as e:
        return None, f"Network error connecting to {host}: {e}"
    except Exception as e:
        return None, f"An unexpected error occurred: {e}"
    return None, "Unknown error"

def get_or_create_session(host, username, password=None, key_filename=None, port=22):
    """
    Retrieves an existing active session or creates a new one if it doesn't exist or is closed.
    Updates the last_activity_time for the session.
    """
    print(f"Checking session for {host} {username} , port {port}")
    with session_lock:
        session_info = active_ssh_sessions.get(host)
        client = session_info['client'] if session_info else None
        
        # Check if the existing client is still active
        if client:
            try:
                transport = client.get_transport()
                if transport and transport.is_active() and transport.send_ignore():
                    print(f"Using existing active session for {host}")
                    # Update activity time since session is being accessed
                    active_ssh_sessions[host]['last_activity_time'] = datetime.datetime.now()
                    return client, None
                else:
                    print(f"Session for {host} found but is not active. Reconnecting...")
                    client.close() # Ensure old transport is closed
                    client, error_msg = create_ssh_session(host, username, password, key_filename, port)
                    if client:
                        active_ssh_sessions[host] = {'client': client, 'last_activity_time': datetime.datetime.now()}
                    return client, error_msg
            except EOFError:
                print(f"Session for {host} unexpectedly closed. Reconnecting...")
                client.close()
                client, error_msg = create_ssh_session(host, username, password, key_filename, port)
                if client:
                    active_ssh_sessions[host] = {'client': client, 'last_activity_time': datetime.datetime.now()}
                return client, error_msg
            except Exception as e:
                print(f"Error checking session for {host}: {e}. Reconnecting...")
                if client:
                    client.close()
                client, error_msg = create_ssh_session(host, username, password, key_filename, port)
                if client:
                    active_ssh_sessions[host] = {'client': client, 'last_activity_time': datetime.datetime.now()}
                return client, host
        else:
            print(f"No existing session for {host}. Creating a new one...")
            client, error_msg = create_ssh_session(host, username, password, key_filename, port)
            if client:
                active_ssh_sessions[host] = {'client': client, 'last_activity_time': datetime.datetime.now()}
            return client, error_msg

def execute_command(host, command):
    """
    Executes a command on the specified SSH session.
    Assumes the session is already managed by get_or_create_session.
    Updates the last_activity_time for the session.
    """
    with session_lock:
        session_info = active_ssh_sessions.get(host)
        if not session_info:
            print(f"No active session for {host}. Please establish a connection first.")
            return None, None, None

        client = session_info['client']
        try:
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            # Update activity time after successful command execution
            active_ssh_sessions[host]['last_activity_time'] = datetime.datetime.now()
            
            return stdin, output, error
        except paramiko.SSHException as e:
            print(f"Error executing command on {host}: {e}")
            return None, None, str(e)
        except Exception as e:
            print(f"An unexpected error occurred while executing command: {e}")
            return None, None, str(e)

def close_session(host):
    """Closes a specific SSH session and removes it from the map."""
    with session_lock:
        session_info = active_ssh_sessions.get(host)
        if session_info:
            client = session_info['client']
            try:
                if client:
                    client.close()
                    print(f"Closed session for {host} due to inactivity or explicit call.")
            except Exception as e:
                print(f"Error closing session for {host}: {e}")
            finally:
                if host in active_ssh_sessions:
                    del active_ssh_sessions[host]

def close_all_sessions():
    """Closes all active SSH sessions."""
    with session_lock:
        # Create a list of IPs to avoid RuntimeError due to dictionary size change during iteration
        hosts_to_close = list(active_ssh_sessions.keys()) 
        for host in hosts_to_close:
            close_session(host)

def session_monitor_thread(host, username, password=None, key_filename=None, port=22, interval=60):
    """
    A separate thread to monitor and keep a specific SSH session alive.
    It will attempt to reconnect if the session goes down.
    This thread is mostly for active keep-alive, not for inactivity timeout.
    """
    while True:
        try:
            # Call get_or_create_session to ensure the session is active and update activity time
            client = get_or_create_session(host, username, password, key_filename, port)
            if client:
                # Optionally, send a lightweight command to keep the session truly alive
                # This helps detect if the connection broke without explicit closure
                _stdin, _stdout, _stderr = client.exec_command("echo KeepAlive", timeout=5)
                _stdout.read() # Read to consume output and complete command
            else:
                print(f"Monitor: Failed to get/create session for {host}. Retrying...")
            
        except Exception as e:
            print(f"Monitor thread error for {host}: {e}. Attempting reconnect on next cycle.")
        
        time.sleep(interval)

def inactivity_cleanup_thread(interval=30):
    """
    A separate thread to periodically check for and close inactive SSH sessions.
    """
    while True:
        current_time = datetime.datetime.now()
        hosts_to_close = []
        
        with session_lock:
            for host, session_info in active_ssh_sessions.items():
                last_activity = session_info['last_activity_time']
                if (current_time - last_activity).total_seconds() > INACTIVITY_TIMEOUT:
                    hosts_to_close.append(host)
        
        for host in hosts_to_close:
            print(f"Session for {host} has been inactive for more than {INACTIVITY_TIMEOUT} seconds. Closing...")
            close_session(host) # Use the single session closer
        
        time.sleep(interval)

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
    # # monitor_thread_1 = threading.Thread(target=session_monitor_thread, args=(server_ip_1, ssh_username_1, ssh_password_1), daemon=True)
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
