"""Node Agent - Distributed scanning node worker.

This script runs on each scanning node and:
1. Registers with the Master server
2. Sends periodic heartbeats
3. Listens for tasks from the Redis queue
4. Executes scan tasks
5. Reports results back to Master
"""

import asyncio
import json
import logging
import os
import psutil
import yaml
import argparse
import sys
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

import aiohttp
import redis.asyncio as redis
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/node_agent.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


class NodeConfig(BaseModel):
    """Node configuration."""

    node: Dict[str, Any]
    master: Dict[str, Any]
    redis: Dict[str, Any]
    performance: Dict[str, Any]
    tools: Dict[str, Any]


class NodeAgent:
    """Distributed scanning node agent."""

    def __init__(self, config_path: str):
        """Initialize node agent with configuration."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.node_id: Optional[int] = None
        self.node_config = self.config.node
        self.master_config = self.config.master
        self.redis_config = self.config.redis
        self.perf_config = self.config.performance

        self.redis_client: Optional[redis.Redis] = None
        self.session: Optional[aiohttp.ClientSession] = None

        logger.info(
            f"Node Agent initialized: {self.node_config['name']} "
            f"({self.node_config['host']}:{self.node_config['port']})"
        )

    def _load_config(self) -> NodeConfig:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, "r") as f:
                config_dict = yaml.safe_load(f)
            return NodeConfig(**config_dict)
        except Exception as e:
            logger.error(f"Failed to load config file {self.config_path}: {e}")
            raise

    async def connect(self) -> bool:
        """Connect to Redis and HTTP session."""
        try:
            # Create HTTP session
            self.session = aiohttp.ClientSession()

            # Connect to Redis
            self.redis_client = await redis.from_url(
                f"redis://{self.redis_config['host']}:{self.redis_config['port']}/{self.redis_config['db']}",
                password=self.redis_config.get("password"),
            )

            # Test Redis connection
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")

            return True

        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis and HTTP session."""
        try:
            if self.redis_client:
                await self.redis_client.close()
                logger.info("Disconnected from Redis")

            if self.session:
                await self.session.close()
                logger.info("Closed HTTP session")

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    async def register_with_master(self) -> bool:
        """Register node with Master server."""
        try:
            register_url = f"{self.master_config['api_url']}/nodes/register"

            payload = {
                "name": self.node_config["name"],
                "host": self.node_config["host"],
                "port": self.node_config["port"],
                "node_type": self.node_config.get("type", "scanner"),
                "max_concurrent_tasks": self.perf_config["max_concurrent_tasks"],
                "api_version": "0.1.0",
            }

            async with self.session.post(register_url, json=payload) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    self.node_id = data["id"]
                    logger.info(f"Successfully registered with Master (Node ID: {self.node_id})")
                    return True
                elif resp.status == 409:
                    # Node already exists, get its ID
                    logger.info(f"Node already registered, retrieving ID...")
                    get_url = f"{self.master_config['api_url']}/nodes"
                    async with self.session.get(get_url) as get_resp:
                        data = await get_resp.json()
                        for node in data.get("nodes", []):
                            if node["name"] == self.node_config["name"]:
                                self.node_id = node["id"]
                                logger.info(f"Retrieved existing Node ID: {self.node_id}")
                                return True
                    return False
                else:
                    text = await resp.text()
                    logger.error(f"Failed to register: {resp.status} - {text}")
                    return False

        except Exception as e:
            logger.error(f"Error registering with Master: {e}")
            return False

    async def send_heartbeat(self) -> bool:
        """Send heartbeat to Master with resource metrics."""
        try:
            if not self.node_id:
                logger.warning("Node not registered, skipping heartbeat")
                return False

            # Gather system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage("/")

            heartbeat_url = f"{self.master_config['api_url']}/nodes/{self.node_id}/heartbeat"

            payload = {
                "status": "online",
                "cpu_usage": cpu_percent,
                "memory_usage": memory_info.percent,
                "disk_usage": disk_info.percent,
                "current_tasks": 0,  # TODO: Track actual task count
            }

            async with self.session.post(heartbeat_url, json=payload) as resp:
                if resp.status == 200:
                    logger.debug(f"Heartbeat sent: CPU={cpu_percent}%, Mem={memory_info.percent}%")
                    return True
                else:
                    logger.warning(f"Heartbeat failed: {resp.status}")
                    return False

        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            return False

    async def check_for_tasks(self) -> None:
        """Check Redis queue for pending tasks."""
        try:
            if not self.redis_client:
                return

            # Get task from queue
            task_json = await self.redis_client.lpop(
                f"node:{self.node_id}:tasks"
            )

            if task_json:
                task = json.loads(task_json)
                logger.info(f"Received task: {task['id']} - {task['name']}")
                await self.execute_task(task)

        except Exception as e:
            logger.error(f"Error checking for tasks: {e}")

    async def execute_task(self, task: Dict[str, Any]) -> None:
        """Execute a scan task."""
        try:
            task_id = task["id"]
            task_type = task.get("type", "port_scan")
            target = task.get("target_range")

            logger.info(f"Executing task {task_id}: {task_type} on {target}")

            # Simulate task execution (in real implementation, call scanning tools)
            result = {
                "task_id": task_id,
                "status": "completed",
                "result": f"Scan completed for {target}",
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Store result in Redis
            await self.redis_client.rpush(
                f"results:{task_id}",
                json.dumps(result),
            )

            logger.info(f"Task {task_id} completed")

        except Exception as e:
            logger.error(f"Error executing task: {e}")

    async def heartbeat_loop(self) -> None:
        """Periodic heartbeat loop."""
        while True:
            try:
                await asyncio.sleep(self.perf_config["heartbeat_interval"])
                await self.send_heartbeat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

    async def task_check_loop(self) -> None:
        """Periodic task checking loop."""
        while True:
            try:
                await asyncio.sleep(self.perf_config["check_task_interval"])
                await self.check_for_tasks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in task check loop: {e}")

    async def run(self) -> None:
        """Run the node agent."""
        try:
            # Create logs directory if it doesn't exist
            Path("logs").mkdir(exist_ok=True)

            # Connect to services
            if not await self.connect():
                logger.error("Failed to connect to services")
                sys.exit(1)

            # Register with Master
            if not await self.register_with_master():
                logger.error("Failed to register with Master")
                sys.exit(1)

            # Start background tasks
            heartbeat_task = asyncio.create_task(self.heartbeat_loop())
            task_check_task = asyncio.create_task(self.task_check_loop())

            logger.info("Node Agent started successfully")

            # Keep running
            await asyncio.gather(heartbeat_task, task_check_task)

        except KeyboardInterrupt:
            logger.info("Node Agent interrupted")
        except Exception as e:
            logger.error(f"Error running Node Agent: {e}")
        finally:
            await self.disconnect()

    async def run_with_timeout(self, timeout: Optional[int] = None) -> None:
        """Run node agent with optional timeout."""
        try:
            if timeout:
                await asyncio.wait_for(self.run(), timeout=timeout)
            else:
                await self.run()
        except asyncio.TimeoutError:
            logger.error("Node Agent timeout")
        except Exception as e:
            logger.error(f"Error in run_with_timeout: {e}")
        finally:
            await self.disconnect()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="CatchCore Node Agent")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to node configuration YAML file",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds (optional)",
    )

    args = parser.parse_args()

    # Create node agent
    agent = NodeAgent(args.config)

    # Run agent
    await agent.run_with_timeout(args.timeout)


if __name__ == "__main__":
    asyncio.run(main())
