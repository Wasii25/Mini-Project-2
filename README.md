# SQL Voice Agent with MCP

Natural language SQL agent using PostgreSQL, MCP protocol, and local LLM (Ollama).

## Prerequisites

### 1. Install System Dependencies
```bash
# PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Node.js (for MCP server)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Python
sudo apt install python3 python3-pip
```

### 2. Install Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull llama3.2:3b
# OR for better accuracy:
# ollama pull phi3:mini
```

### 3. Install Official PostgreSQL MCP Server
```bash
npm install -g @modelcontextprotocol/server-postgres
```

## Setup

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd <your-repo-name>
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup PostgreSQL Database
```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << 'EOF'
CREATE USER student_user WITH PASSWORD 'student123';
CREATE DATABASE student_db OWNER student_user;
\c student_db
GRANT ALL ON SCHEMA public TO student_user;
\q
EOF

# Load sample data
sudo -u postgres psql -d student_db -f schema.sql
```

### 4. Verify Setup
```bash
# Test PostgreSQL connection
PGPASSWORD=student123 psql -h localhost -U student_user -d student_db -c "SELECT COUNT(*) FROM students;"

# Test Ollama
curl http://localhost:11434/api/tags

# Test MCP server
which mcp-server-postgres
```

## Run
```bash
python postgres_agent.py
```

## Usage
```
Question: list all students
Question: show me students in CS201
Question: which course has the most enrollments
Question: exit
```

## Project Structure
```
.
├── postgres_agent.py      # Main agent code
├── schema.sql            # Database schema and sample data
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Configuration

Edit `postgres_agent.py` to change:

- **Model**: Line 18 - Change `llama3.2:3b` to `phi3:mini` for better accuracy
- **Database**: Line 16 - Update connection string if using different credentials
- **Verbose mode**: Line 372 - Set `verbose_mode = True` for debugging

## Troubleshooting

### "mcp-server-postgres: command not found"
```bash
npm install -g @modelcontextprotocol/server-postgres
```

### "Peer authentication failed"
Edit `/etc/postgresql/*/main/pg_hba.conf`:
```
# Change from:
local   all   all   peer

# To:
local   all   all   md5
```
Then restart: `sudo systemctl restart postgresql`

### "Ollama connection refused"
```bash
sudo systemctl start ollama
# OR
ollama serve
```

## Features

- ✅ Natural language to SQL
- ✅ PostgreSQL database queries
- ✅ MCP protocol for reliable execution
- ✅ 100% offline (after initial setup)
- ✅ Clean, voice-friendly output

## Future Enhancements

- [ ] Voice input (STT with Vosk)
- [ ] Voice output (TTS with Coqui)
- [ ] Query caching
- [ ] Monitoring dashboard
- [ ] Performance metrics

## License

MIT
