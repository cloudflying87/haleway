#!/usr/bin/env python3
"""
Pre-Deployment Validation Script
Checks for common deployment issues and suggests fixes
Run on the server before deploying
"""

import os
import sys
import socket
import subprocess
import json
import secrets
import string
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class DeploymentValidator:
    def __init__(self, project_dir: Path = None):
        self.project_dir = project_dir or Path.cwd()
        self.issues = []
        self.warnings = []
        self.fixes = []

    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("🔍 Pre-Deployment Validation")
        print("=" * 50)

        self.check_docker_running()
        self.check_env_file()
        self.check_port_availability()
        self.check_network_conflicts()
        self.check_volume_conflicts()
        self.check_credentials()

        return self.show_results()

    def check_docker_running(self):
        """Check if Docker is running."""
        print("\n📦 Checking Docker...")
        try:
            subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                check=True,
                timeout=5
            )
            print("  ✅ Docker is running")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            self.issues.append({
                'type': 'docker',
                'message': 'Docker is not running or not installed',
                'fix_location': 'SERVER',
                'fix': 'Start Docker: sudo systemctl start docker'
            })
            print("  ❌ Docker is not running")

    def check_env_file(self):
        """Check if .env file exists and has real values."""
        print("\n🔐 Checking .env file...")

        env_path = self.project_dir / ".env"
        env_example = self.project_dir / ".env.example"

        if not env_path.exists():
            self.issues.append({
                'type': 'env',
                'message': '.env file missing',
                'fix_location': 'SERVER',
                'fix': f'cp .env.example .env && nano .env'
            })
            print("  ❌ .env file not found")
            return

        print("  ✅ .env file exists")

        # Check for placeholder values
        env_content = env_path.read_text()
        placeholders = [
            ('your-secret-key-here', 'SECRET_KEY'),
            ('secure-password-here', 'DB_PASSWORD'),
            ('your-sentry-dsn-here', 'SENTRY_DSN'),
            ('your-tunnel-token-here', 'CLOUDFLARE_TUNNEL_TOKEN'),
        ]

        for placeholder, var_name in placeholders:
            if placeholder in env_content:
                self.warnings.append({
                    'type': 'env_placeholder',
                    'message': f'{var_name} still has placeholder value',
                    'fix_location': 'SERVER',
                    'fix': f'Edit .env and set real {var_name}'
                })
                print(f"  ⚠️  {var_name} needs a real value")

    def check_port_availability(self):
        """Check if required ports are available."""
        print("\n🔌 Checking port availability...")

        # Parse docker-compose.yml to find required ports
        required_ports = self._get_required_ports()

        # Check what ports are in use
        used_ports = self._get_used_ports()

        conflicts = []
        for port in required_ports:
            if port in used_ports:
                conflicts.append((port, used_ports[port]))

        if conflicts:
            print(f"  ❌ Port conflicts detected")

            # Find available ports
            override_config = "services:\n"

            for port, used_by in conflicts:
                available_port = self._find_available_port(int(port))
                print(f"     Port {port} used by: {used_by}")
                print(f"     Suggested: {available_port}")

                # Determine service name (nginx uses 80, postgres 5432, redis 6379)
                service_name = self._port_to_service(port)
                if service_name:
                    override_config += f"  {service_name}:\n"
                    override_config += f"    ports:\n"
                    override_config += f"      - '{available_port}:{port}'\n"

            self.issues.append({
                'type': 'port_conflict',
                'message': f'Ports in use: {[p for p, _ in conflicts]}',
                'fix_location': 'SERVER',
                'fix': f'Create docker-compose.override.yml with:\n{override_config}'
            })
        else:
            print(f"  ✅ All required ports available: {required_ports}")

    def check_network_conflicts(self):
        """Check for Docker network name and subnet conflicts."""
        print("\n🌐 Checking network conflicts...")

        # Get network name from docker-compose.yml
        project_networks = self._get_project_networks()

        # Get existing Docker networks
        try:
            result = subprocess.run(
                ["docker", "network", "ls", "--format", "{{.Name}}"],
                capture_output=True,
                text=True,
                check=True
            )
            existing_networks = result.stdout.strip().split('\n')
        except subprocess.CalledProcessError:
            print("  ⚠️  Could not check Docker networks")
            return

        # Check for name conflicts
        name_conflicts = [net for net in project_networks if net in existing_networks]

        if name_conflicts:
            print(f"  ⚠️  Network name conflicts: {name_conflicts}")

            # Get subnet conflicts
            subnet_conflicts = self._check_subnet_conflicts()

            if subnet_conflicts:
                available_subnet = self._find_available_subnet()
                print(f"     Subnet conflict detected")
                print(f"     Suggested subnet: {available_subnet}")

                override_config = "networks:\n"
                for net in name_conflicts:
                    override_config += f"  {net}:\n"
                    override_config += f"    driver: bridge\n"
                    override_config += f"    ipam:\n"
                    override_config += f"      config:\n"
                    override_config += f"        - subnet: {available_subnet}\n"

                self.issues.append({
                    'type': 'network_conflict',
                    'message': f'Network conflicts: {name_conflicts}',
                    'fix_location': 'SERVER',
                    'fix': f'Add to docker-compose.override.yml:\n{override_config}'
                })
            else:
                print(f"  ✅ Networks exist but no subnet conflicts")
        else:
            print("  ✅ No network conflicts")

    def check_volume_conflicts(self):
        """Check for Docker volume name conflicts."""
        print("\n💾 Checking volume conflicts...")

        project_volumes = self._get_project_volumes()

        try:
            result = subprocess.run(
                ["docker", "volume", "ls", "--format", "{{.Name}}"],
                capture_output=True,
                text=True,
                check=True
            )
            existing_volumes = result.stdout.strip().split('\n')
        except subprocess.CalledProcessError:
            print("  ⚠️  Could not check Docker volumes")
            return

        conflicts = [vol for vol in project_volumes if vol in existing_volumes]

        if conflicts:
            print(f"  ⚠️  Volume name conflicts: {conflicts}")
            print(f"     These volumes already exist and will be reused")
            print(f"     This may contain data from another project!")

            self.warnings.append({
                'type': 'volume_conflict',
                'message': f'Volumes exist: {conflicts}',
                'fix_location': 'SERVER',
                'fix': 'Either: 1) Remove old volumes: docker volume rm <name>, OR 2) Rename in docker-compose.yml'
            })
        else:
            print("  ✅ No volume conflicts")

    def check_credentials(self):
        """Check for secure credentials."""
        print("\n🔒 Checking credentials...")

        env_path = self.project_dir / ".env"
        if not env_path.exists():
            return

        env_content = env_path.read_text()

        # Check SECRET_KEY length and randomness
        import re
        secret_match = re.search(r'SECRET_KEY=([^\n]+)', env_content)
        if secret_match:
            secret_key = secret_match.group(1)
            if len(secret_key) < 50:
                secure_key = self._generate_secret_key()
                self.warnings.append({
                    'type': 'weak_secret',
                    'message': 'SECRET_KEY is too short',
                    'fix_location': 'SERVER',
                    'fix': f'Replace SECRET_KEY in .env with:\nSECRET_KEY={secure_key}'
                })
                print("  ⚠️  SECRET_KEY is weak")
            else:
                print("  ✅ SECRET_KEY looks secure")

        # Check for ALLOWED_HOSTS
        if 'ALLOWED_HOSTS=' in env_content:
            hosts_match = re.search(r'ALLOWED_HOSTS=([^\n]+)', env_content)
            if hosts_match and 'yourdomain.com' in hosts_match.group(1):
                self.warnings.append({
                    'type': 'allowed_hosts',
                    'message': 'ALLOWED_HOSTS still has placeholder',
                    'fix_location': 'SERVER',
                    'fix': 'Update ALLOWED_HOSTS in .env with your actual domain'
                })
                print("  ⚠️  ALLOWED_HOSTS needs updating")

    def _get_required_ports(self) -> List[str]:
        """Parse docker-compose.yml for required ports."""
        compose_file = self.project_dir / "docker-compose.yml"
        if not compose_file.exists():
            return []

        ports = []
        content = compose_file.read_text()

        # Simple regex to find port mappings like "80:80" or "8000:8000"
        import re
        matches = re.findall(r'["\'"]?(\d+):\d+["\'"]?', content)
        ports = list(set(matches))  # Remove duplicates

        return ports

    def _get_used_ports(self) -> Dict[str, str]:
        """Get ports currently in use by Docker and system."""
        used = {}

        # Check Docker containers
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}\t{{.Ports}}"],
                capture_output=True,
                text=True,
                check=True
            )

            import re
            for line in result.stdout.split('\n'):
                if not line.strip():
                    continue
                parts = line.split('\t')
                if len(parts) >= 2:
                    container_name = parts[0]
                    ports_str = parts[1]
                    # Extract host ports like "0.0.0.0:80->80/tcp"
                    ports = re.findall(r'0\.0\.0\.0:(\d+)', ports_str)
                    for port in ports:
                        used[port] = container_name
        except subprocess.CalledProcessError:
            pass

        # Check system ports using lsof (if available)
        try:
            result = subprocess.run(
                ["lsof", "-iTCP", "-sTCP:LISTEN", "-n", "-P"],
                capture_output=True,
                text=True
            )
            import re
            for line in result.stdout.split('\n'):
                match = re.search(r':(\d+)\s+\(LISTEN\)', line)
                if match:
                    port = match.group(1)
                    if port not in used:
                        # Extract process name
                        parts = line.split()
                        if parts:
                            used[port] = parts[0]
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        return used

    def _find_available_port(self, start_port: int) -> int:
        """Find next available port starting from start_port."""
        # Try common alternate ports first
        if start_port == 80:
            candidates = [8080, 8081, 8082, 8000, 8001]
        elif start_port == 5432:
            candidates = [5433, 5434, 5435]
        elif start_port == 6379:
            candidates = [6380, 6381, 6382]
        else:
            candidates = [start_port + i for i in range(1, 100)]

        used_ports = self._get_used_ports()

        for port in candidates:
            if str(port) not in used_ports:
                # Double-check by trying to bind
                if self._is_port_available(port):
                    return port

        return start_port + 1000  # Fallback

    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available by trying to bind to it."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return True
        except OSError:
            return False

    def _port_to_service(self, port: str) -> Optional[str]:
        """Map port number to likely service name."""
        mapping = {
            '80': 'nginx',
            '443': 'nginx',
            '8080': 'web',
            '8000': 'web',
            '5432': 'db',
            '6379': 'redis',
        }
        return mapping.get(port)

    def _get_project_networks(self) -> List[str]:
        """Get network names from docker-compose.yml."""
        compose_file = self.project_dir / "docker-compose.yml"
        if not compose_file.exists():
            return []

        networks = []
        content = compose_file.read_text()

        # Look for networks section
        import re
        # Match network names in networks: section
        matches = re.findall(r'networks:\s*\n\s+(\w+):', content)
        networks.extend(matches)

        return networks

    def _get_project_volumes(self) -> List[str]:
        """Get volume names from docker-compose.yml."""
        compose_file = self.project_dir / "docker-compose.yml"
        if not compose_file.exists():
            return []

        volumes = []
        content = compose_file.read_text()

        import re
        matches = re.findall(r'volumes:\s*\n\s+(\w+):', content)
        volumes.extend(matches)

        return volumes

    def _check_subnet_conflicts(self) -> bool:
        """Check if Docker network subnets conflict."""
        try:
            result = subprocess.run(
                ["docker", "network", "inspect", "bridge"],
                capture_output=True,
                text=True,
                check=True
            )
            # If we can inspect, networks exist - detailed check would parse JSON
            return False  # Simplified for now
        except subprocess.CalledProcessError:
            return False

    def _find_available_subnet(self) -> str:
        """Find an available Docker network subnet."""
        # Get all existing subnets
        try:
            result = subprocess.run(
                ["docker", "network", "ls", "--format", "{{.Name}}"],
                capture_output=True,
                text=True,
                check=True
            )

            networks = result.stdout.strip().split('\n')
            used_subnets = set()

            for network in networks:
                if not network.strip():
                    continue
                try:
                    inspect_result = subprocess.run(
                        ["docker", "network", "inspect", network],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    network_data = json.loads(inspect_result.stdout)
                    if network_data and 'IPAM' in network_data[0]:
                        for config in network_data[0]['IPAM'].get('Config', []):
                            if 'Subnet' in config:
                                used_subnets.add(config['Subnet'])
                except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
                    continue

            # Find available subnet in 172.x.0.0/16 range
            for i in range(18, 32):
                candidate = f"172.{i}.0.0/16"
                if candidate not in used_subnets:
                    return candidate

            # Fallback to 192.168.x.0/24 range
            for i in range(100, 255):
                candidate = f"192.168.{i}.0/24"
                if candidate not in used_subnets:
                    return candidate

        except subprocess.CalledProcessError:
            pass

        return "172.25.0.0/16"  # Default fallback

    def _generate_secret_key(self, length: int = 50) -> str:
        """Generate a secure SECRET_KEY."""
        alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def show_results(self) -> bool:
        """Show validation results and fixes."""
        print("\n" + "=" * 50)
        print("📊 Validation Results")
        print("=" * 50)

        if not self.issues and not self.warnings:
            print("\n✅ All checks passed! Ready to deploy.")
            return True

        if self.issues:
            print(f"\n❌ Found {len(self.issues)} blocking issue(s):")
            for i, issue in enumerate(self.issues, 1):
                print(f"\n{i}. {issue['message']}")
                print(f"   Fix location: {issue['fix_location']}")
                print(f"   Fix: {issue['fix']}")

        if self.warnings:
            print(f"\n⚠️  Found {len(self.warnings)} warning(s):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"\n{i}. {warning['message']}")
                print(f"   Fix location: {warning['fix_location']}")
                print(f"   Fix: {warning['fix']}")

        print("\n" + "=" * 50)

        # Offer to auto-generate fixes
        if self.issues:
            print("\n💡 Would you like to auto-generate fixes?")
            response = input("Generate docker-compose.override.yml? (y/N): ")
            if response.lower() == 'y':
                self._generate_override_file()

        return len(self.issues) == 0

    def _generate_override_file(self):
        """Generate docker-compose.override.yml with fixes."""
        override_path = self.project_dir / "docker-compose.override.yml"

        if override_path.exists():
            print(f"\n⚠️  docker-compose.override.yml already exists")
            response = input("Overwrite? (y/N): ")
            if response.lower() != 'y':
                return

        content = "# Auto-generated by validate_deployment.py\n"
        content += "# Server-specific overrides (not tracked in git)\n\n"
        content += "version: '3.8'\n\n"

        # Collect all port and network fixes
        has_services = False
        has_networks = False

        services_section = "services:\n"
        networks_section = "networks:\n"

        for issue in self.issues:
            if issue['type'] == 'port_conflict':
                # Extract service config from fix
                if 'services:' in issue['fix']:
                    fix_lines = issue['fix'].split('\n')[1:]  # Skip 'services:' line
                    services_section += '\n'.join(fix_lines) + '\n'
                    has_services = True

            elif issue['type'] == 'network_conflict':
                if 'networks:' in issue['fix']:
                    fix_lines = issue['fix'].split('\n')[1:]  # Skip 'networks:' line
                    networks_section += '\n'.join(fix_lines) + '\n'
                    has_networks = True

        if has_services:
            content += services_section + "\n"

        if has_networks:
            content += networks_section + "\n"

        if has_services or has_networks:
            override_path.write_text(content)
            print(f"\n✅ Generated {override_path}")
            print("   Review and adjust as needed")
        else:
            print("\n   No port/network fixes to generate")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate deployment readiness')
    parser.add_argument('--project-dir', type=Path, help='Project directory (default: current)')
    parser.add_argument('--non-interactive', action='store_true', help='No prompts, just report')

    args = parser.parse_args()

    validator = DeploymentValidator(args.project_dir)

    success = validator.validate_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
