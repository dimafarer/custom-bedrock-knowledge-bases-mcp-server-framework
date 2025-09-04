# MCP Bedrock Knowledge Base Server (Strands)

> **Note:** This README is written for Amazon Q CLI version 1.14.1. Command syntax may differ in other versions.

A minimal Model Context Protocol (MCP) server that connects to AWS Bedrock Knowledge Base for Strands-specific documentation queries.

## ⚠️ Important: Tool and Server Naming

This server provides:
- **Server Name**: `bedrock-kb` 
- **Tool Name**: `query_strands_knowledge_base`

**Critical**: If you're running multiple MCP servers, each MUST have unique server names and tool names to avoid conflicts in Q CLI. Simply pointing to different knowledge bases is NOT sufficient - the tool names must be different.

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy the example environment file and fill in your values:
```bash
cp .env.example .env
```

Edit `.env` with your AWS Bedrock Knowledge Base details:
```
BEDROCK_KB_ID=your-knowledge-base-id-here
AWS_REGION=your-aws-region
BEDROCK_MODEL_ARN=arn:aws:bedrock:your-region::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0
```

### 3. Configure AWS Credentials
Ensure your AWS credentials are configured via:
- AWS CLI: `aws configure`
- Environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- IAM roles (if running on EC2)

Required permissions:
- `bedrock:RetrieveAndGenerate`

### 4. Run the Server
```bash
python src/mcp_bedrock_kb/server.py
```

## Integration with Amazon Q CLI

### Method 1: Using Q CLI MCP Commands (Recommended)

1. **Add the MCP server using Q CLI:**
```bash
q mcp add --name bedrock-kb --command python --args /path/to/your/mcp-bedrock-kb/src/mcp_bedrock_kb/server.py --env BEDROCK_KB_ID=your-knowledge-base-id --env AWS_REGION=your-aws-region --env BEDROCK_MODEL_ARN=arn:aws:bedrock:your-region::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0
```

Replace `/path/to/your/mcp-bedrock-kb/` with the actual path to your cloned repository and `your-knowledge-base-id` with your actual Bedrock Knowledge Base ID.

2. **Verify the server is added:**
```bash
q mcp list
```

3. **Test the integration:**
```bash
q chat
# In the chat, you can now use: query_knowledge_base("your question here")
```

### Method 2: Manual Configuration File Editing

1. **Locate your Q CLI configuration file:**
```bash
# Configuration is typically at:
~/.aws/amazonq/mcp.json
```

2. **Edit the configuration file to add the MCP server:**
```json
{
  "mcpServers": {
    "bedrock-kb": {
      "command": "python",
      "args": ["/path/to/your/mcp-bedrock-kb/src/mcp_bedrock_kb/server.py"],
      "env": {
        "BEDROCK_KB_ID": "your-knowledge-base-id-here",
        "AWS_REGION": "your-aws-region",
        "BEDROCK_MODEL_ARN": "arn:aws:bedrock:your-region::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
      }
    }
  }
}
```

3. **Restart Q CLI to load the new configuration:**
```bash
q chat
```

## Usage with MCP Clients

The server provides one tool:
- `query_strands_knowledge_base`: Query the configured Strands Bedrock Knowledge Base

### Available Tool

**query_strands_knowledge_base(query: str) -> str**
- Queries the configured AWS Bedrock Knowledge Base for Strands documentation
- Returns relevant information based on the query
- Automatically handles retrieval and generation using the configured model

## Example Usage in Q CLI

Once integrated, you can use the Strands knowledge base tool in your Q CLI conversations:

```
User: Can you query the Strands knowledge base about best practices?

Q: I'll query the Strands knowledge base for information about best practices.

query_strands_knowledge_base("best practices and implementation patterns")

Based on the Strands knowledge base, here are the key best practices...
```

## Troubleshooting

### Common Issues

1. **"Server not found" error:**
   - Verify the path to `server.py` is correct
   - Ensure Python can find the required dependencies
   - Check that the virtual environment is activated if using one

2. **AWS permissions error:**
   - Verify AWS credentials are configured
   - Ensure the IAM user/role has `bedrock:RetrieveAndGenerate` permission
   - Check that the Knowledge Base ID exists and is accessible

3. **Environment variables not loaded:**
   - Ensure `.env` file is in the correct location
   - Verify environment variable names match exactly
   - For manual config, ensure env vars are in the JSON configuration

### Debugging

Enable debug logging by setting:
```bash
export MCP_DEBUG=1
```

Check Q CLI logs:
```bash
q chat --verbose
```
