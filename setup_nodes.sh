#!/bin/bash

# CatchCore Node Setup Script
# This script helps deploy and configure CatchCore scanning nodes
# Usage: ./setup_nodes.sh [action] [options]

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MASTER_HOST="${MASTER_HOST:-localhost}"
MASTER_PORT="${MASTER_PORT:-8000}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Helper functions
print_header() {
    echo -e "${BLUE}==== $1 ====${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    local missing=0

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        missing=1
    else
        print_success "Python 3 found: $(python3 --version)"
    fi

    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is required but not installed"
        missing=1
    else
        print_success "pip3 found"
    fi

    # Check git
    if ! command -v git &> /dev/null; then
        print_warning "Git not found (optional for development)"
    else
        print_success "Git found: $(git --version)"
    fi

    # Check Docker (optional)
    if command -v docker &> /dev/null; then
        print_success "Docker found: $(docker --version)"
    else
        print_warning "Docker not found (optional, required for containerized deployment)"
    fi

    if [ $missing -eq 1 ]; then
        print_error "Please install missing prerequisites"
        exit 1
    fi

    echo ""
}

# Setup single node
setup_single_node() {
    local node_name=$1
    local node_type=${2:-scanner}
    local node_port=${3:-8001}
    local max_tasks=${4:-5}

    print_header "Setting Up Node: $node_name"

    # Create node configuration directory
    local config_dir="$PROJECT_ROOT/node_configs"
    mkdir -p "$config_dir"

    # Create node-specific configuration
    local config_file="$config_dir/${node_name}.yml"

    cat > "$config_file" << EOF
# Node configuration for $node_name
node:
  name: "$node_name"
  type: "$node_type"
  host: "0.0.0.0"
  port: $node_port

master:
  host: "$MASTER_HOST"
  port: $MASTER_PORT
  api_url: "http://$MASTER_HOST:$MASTER_PORT/api/v1"

redis:
  host: "$REDIS_HOST"
  port: $REDIS_PORT
  db: 0
  password: null

performance:
  max_concurrent_tasks: $max_tasks
  worker_threads: 4
  heartbeat_interval: 30
  check_task_interval: 5

tools:
  fscan_enabled: true
  nuclei_enabled: true
  afrog_enabled: true
  dddd_enabled: true
  dirsearch_enabled: true
  auto_install: true
EOF

    print_success "Created configuration: $config_file"
    echo ""
}

# Setup multiple nodes
setup_multiple_nodes() {
    local num_scanners=${1:-2}
    local num_workers=${2:-1}

    print_header "Setting Up Multiple Nodes"
    echo "Scanner nodes: $num_scanners"
    echo "Worker nodes: $num_workers"
    echo ""

    local port=8001

    # Create scanner nodes
    for ((i=1; i<=num_scanners; i++)); do
        local node_name="scanner-node-$(printf "%02d" $i)"
        setup_single_node "$node_name" "scanner" "$port" 5
        port=$((port + 1))
    done

    # Create worker nodes
    for ((i=1; i<=num_workers; i++)); do
        local node_name="worker-node-$(printf "%02d" $i)"
        setup_single_node "$node_name" "worker" "$port" 3
        port=$((port + 1))
    done

    print_success "All nodes configured"
    echo ""
}

# Create data directories
create_data_dirs() {
    print_header "Creating Data Directories"

    local config_dir="$PROJECT_ROOT/node_configs"
    mkdir -p "$config_dir"

    # Get list of configured nodes
    for config_file in "$config_dir"/*.yml; do
        if [ -f "$config_file" ]; then
            local node_name=$(basename "$config_file" .yml)
            local data_dir="$PROJECT_ROOT/data/$node_name"
            mkdir -p "$data_dir"/{logs,data}
            print_success "Created directories for $node_name"
        fi
    done

    # Create main logs directory
    mkdir -p "$PROJECT_ROOT/logs/nodes"
    print_success "Created main logs directory"
    echo ""
}

# Install Python dependencies
install_dependencies() {
    print_header "Installing Python Dependencies"

    cd "$PROJECT_ROOT/backend"

    # Check if venv exists
    if [ ! -d "venv" ]; then
        print_warning "Virtual environment not found, creating..."
        python3 -m venv venv
    fi

    # Activate venv
    source venv/bin/activate

    # Install requirements
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install pyyaml psutil aiohttp redis

    print_success "Dependencies installed"
    deactivate
    echo ""
}

# Start single node
start_node() {
    local node_name=$1
    local config_file="$PROJECT_ROOT/node_configs/${node_name}.yml"

    if [ ! -f "$config_file" ]; then
        print_error "Configuration file not found: $config_file"
        return 1
    fi

    print_header "Starting Node: $node_name"

    cd "$PROJECT_ROOT/backend"
    source venv/bin/activate

    python3 node_agent.py --config "$config_file"

    deactivate
}

# Start all nodes (background)
start_all_nodes() {
    print_header "Starting All Nodes"

    cd "$PROJECT_ROOT/backend"
    source venv/bin/activate

    local config_dir="$PROJECT_ROOT/node_configs"
    for config_file in "$config_dir"/*.yml; do
        if [ -f "$config_file" ]; then
            local node_name=$(basename "$config_file" .yml)
            print_success "Starting $node_name..."
            python3 node_agent.py --config "$config_file" >> "$PROJECT_ROOT/logs/nodes/${node_name}.log" 2>&1 &
        fi
    done

    deactivate
    print_success "All nodes started"
    echo ""
}

# Build Docker image
build_docker_image() {
    print_header "Building Docker Node Image"

    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        return 1
    fi

    cd "$PROJECT_ROOT"
    docker build -f Dockerfile.node -t catchcore-node:latest .

    print_success "Docker image built: catchcore-node:latest"
    echo ""
}

# Start Docker containers
start_docker_nodes() {
    local num_scanners=${1:-2}
    local num_workers=${2:-1}

    print_header "Starting Docker Nodes"

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        return 1
    fi

    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.yml -f docker-compose.nodes.yml up -d

    print_success "Docker nodes started"
    echo "View node status with: docker-compose ps"
    echo "View node logs with: docker-compose logs -f scanner-node-1"
    echo ""
}

# Check node status
check_node_status() {
    print_header "Checking Node Status"

    local api_url="http://$MASTER_HOST:$MASTER_PORT/api/v1/nodes"

    if ! command -v curl &> /dev/null; then
        print_warning "curl is not installed, cannot check node status"
        return
    fi

    echo "Fetching node status from: $api_url"
    echo ""

    local response=$(curl -s "$api_url" 2>/dev/null || echo "")

    if [ -z "$response" ]; then
        print_error "Cannot connect to Master at $MASTER_HOST:$MASTER_PORT"
        return 1
    fi

    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    echo ""
}

# Display help
show_help() {
    cat << EOF
${BLUE}CatchCore Node Setup Script${NC}

${GREEN}Usage:${NC}
    ./setup_nodes.sh [action] [options]

${GREEN}Actions:${NC}
    check               Check prerequisites
    create-single       Create single node configuration
    create-multi        Create multiple nodes
    install-deps        Install Python dependencies
    start-single        Start single node (foreground)
    start-all           Start all nodes (background)
    build-docker        Build Docker node image
    start-docker        Start nodes with Docker
    status              Check node status from Master
    help                Show this help message

${GREEN}Examples:${NC}
    # Check prerequisites
    ./setup_nodes.sh check

    # Create 3 scanner nodes and 1 worker node
    ./setup_nodes.sh create-multi 3 1

    # Install dependencies
    ./setup_nodes.sh install-deps

    # Start all nodes in background
    ./setup_nodes.sh start-all

    # Start Docker nodes
    ./setup_nodes.sh build-docker
    ./setup_nodes.sh start-docker

    # Check node status
    ./setup_nodes.sh status

${GREEN}Configuration:${NC}
    MASTER_HOST         Master server hostname/IP (default: localhost)
    MASTER_PORT         Master API port (default: 8000)
    REDIS_HOST          Redis server hostname/IP (default: localhost)
    REDIS_PORT          Redis port (default: 6379)

${GREEN}Examples:${NC}
    # Deploy nodes to remote master
    MASTER_HOST=192.168.1.50 REDIS_HOST=192.168.1.50 ./setup_nodes.sh create-multi 5 2

EOF
}

# Main script logic
main() {
    local action="${1:-help}"

    case "$action" in
        check)
            check_prerequisites
            ;;
        create-single)
            check_prerequisites
            local node_name="${2:-scanner-node-01}"
            local node_type="${3:-scanner}"
            local node_port="${4:-8001}"
            setup_single_node "$node_name" "$node_type" "$node_port"
            create_data_dirs
            ;;
        create-multi)
            check_prerequisites
            local num_scanners="${2:-2}"
            local num_workers="${3:-1}"
            setup_multiple_nodes "$num_scanners" "$num_workers"
            create_data_dirs
            ;;
        install-deps)
            check_prerequisites
            install_dependencies
            ;;
        start-single)
            local node_name="${2:-scanner-node-01}"
            start_node "$node_name"
            ;;
        start-all)
            start_all_nodes
            check_node_status
            ;;
        build-docker)
            check_prerequisites
            build_docker_image
            ;;
        start-docker)
            check_prerequisites
            build_docker_image
            start_docker_nodes
            ;;
        status)
            check_node_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown action: $action"
            echo "Run './setup_nodes.sh help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
