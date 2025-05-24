"""Docker configuration module"""
import os
import docker

# app/services/docker_config.py

def get_docker_client():
    """
    Returns a Docker client configured correctly for the environment.
    Handles various connection methods and ensures compatibility.
    """
    try:
        # First attempt: try default environment (migliore per container)
        client = docker.from_env()
        client.ping()
        return client
    except Exception as e:
        print(f"Could not connect to Docker with from_env(): {str(e)}")
        
        try:
            # Second attempt: try with explicit unix socket
            client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
            client.ping()
            return client
        except Exception as e:
            print(f"Could not connect to Docker with unix socket: {str(e)}")
            
            try:
                # Third attempt: try with TCP connection to host
                client = docker.DockerClient(base_url='tcp://host.docker.internal:2375')
                client.ping()
                return client
            except Exception as e:
                print(f"Could not connect to Docker with TCP: {str(e)}")
                
                # If all attempts fail, raise an exception
                raise ConnectionError("Could not connect to Docker daemon with any method")