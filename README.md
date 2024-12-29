# SwiftDocsAI Documentation

## Table of Contents
1. [Overview](#1-overview)
2. [System Architecture](#2-system-architecture)
3. [Components](#3-components)
4. [Installation & Deployment](#4-installation--deployment)
5. [Configuration](#5-configuration)
6. [Usage](#6-usage)
7. [API Reference](#7-api-reference)
8. [Security Considerations](#8-security-considerations)
9. [Monitoring & Logging](#9-monitoring--logging)
10. [Troubleshooting](#10-troubleshooting)
11. [Development Guide](#11-development-guide)
12. [Maintenance & Operations](#12-maintenance--operations)

### 1. Overview

SwiftDocsAI is an automated documentation generation tool designed to create comprehensive technical documentation for software projects. It leverages the power of AI, specifically the Claude model from Anthropic, to analyze source code and project files, generating detailed and structured documentation.

Key features:
- Automated processing of multiple file types
- Intelligent chunking and consolidation of content
- Parallel or sequential processing based on project size
- Integration with AWS Bedrock for AI model invocation
- Customizable output and exclusion rules

The tool addresses the challenge of maintaining up-to-date and comprehensive documentation for complex software projects, saving developers time and ensuring consistency across documentation.

### 2. System Architecture

SwiftDocsAI follows a modular architecture designed for flexibility and scalability. The high-level architecture consists of the following main components:

1. File Processing Module
2. Chunking and Consolidation Module
3. AI Integration Module (AWS Bedrock Client)
4. Output Generation Module

Here's a diagram illustrating the architecture:

```
[File System] -> [File Processing Module] -> [Chunking Module]
                                                    |
                                                    v
[AWS Bedrock] <-> [AI Integration Module] <-> [Consolidation Module]
                                                    |
                                                    v
                                           [Output Generation Module]
                                                    |
                                                    v
                                           [Generated Documentation]
```

The system reads files from the specified directory, processes them into manageable chunks, sends these chunks to the AI model for analysis and documentation generation, and then consolidates the results into a final output document.

### 3. Components

#### 3.1 File Processing Module

Purpose: To read and prepare project files for documentation generation.

Core functionality:
- Traverse specified directory and subdirectories
- Apply file extension filters and exclusion rules
- Read file contents and prepare for chunking

Technologies used:
- Python's built-in `os` and `io` modules

Interactions:
- Provides processed file content to the Chunking Module

#### 3.2 Chunking and Consolidation Module

Purpose: To break down large files into manageable chunks and later consolidate AI-generated responses.

Core functionality:
- Split file contents into chunks based on character and word limits
- Combine small chunks to optimize API requests
- Merge AI-generated responses for final output

Technologies used:
- Custom Python algorithms for text splitting and merging

Interactions:
- Receives file content from File Processing Module
- Sends chunks to AI Integration Module
- Receives and consolidates responses from AI Integration Module

#### 3.3 AI Integration Module

Purpose: To interface with the Claude AI model via AWS Bedrock for documentation generation.

Core functionality:
- Prepare and send API requests to AWS Bedrock
- Handle rate limiting and retries
- Process AI model responses

Technologies used:
- `boto3` library for AWS SDK
- AWS Bedrock Runtime API

Interactions:
- Receives chunks from Chunking Module
- Sends requests to AWS Bedrock
- Returns AI-generated content to Consolidation Module

#### 3.4 Output Generation Module

Purpose: To create the final documentation file.

Core functionality:
- Format and structure the consolidated AI-generated content
- Write the final documentation to a Markdown file

Technologies used:
- Python's built-in file handling capabilities

Interactions:
- Receives consolidated content from Consolidation Module
- Outputs final documentation file to the file system

### 4. Installation & Deployment

To set up SwiftDocsAI, follow these steps:

1. Clone the repository:
   ```
   git clone https://github.com/mohammaddaoudfarooqi/SwiftDocsAI.git
   cd SwiftDocsAI
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up AWS credentials:
   - Create an AWS account if you don't have one
   - Create an IAM user with permissions for AWS Bedrock
   - Configure AWS CLI or set environment variables with your credentials

5. Create a `.env` file in the project root and add your AWS credentials:
   ```
   AWS_ACCESS_KEY_ID=your_access_key_id
   AWS_SECRET_ACCESS_KEY=your_secret_access_key
   ```

6. Ensure you have Python 3.10 or later installed.

### 5. Configuration

SwiftDocsAI uses environment variables and script-level constants for configuration:

#### Environment Variables

Create a `.env` file in the project root with the following variables:

```
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
```

#### Script Constants

In `main.py`, you can modify the following constants:

```python
DIRECTORY = "/path/to/your/project"
FILE_EXTENSIONS = [".ts", ".js", ".py", ".ksh", ".yaml", ".md", "Dockerfile", ".yml", ".txt", ".env"]
EXCLUDE_FOLDERS = [".git", ".venv", "node_modules", "logs"]
EXCLUDE_FILES = ["README.md", "LICENSE", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", ".DS_Store"]
OUTPUT_FILE = "README.md"
MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"
```

- `DIRECTORY`: The root directory of the project to document
- `FILE_EXTENSIONS`: List of file extensions to include (empty list for all files)
- `EXCLUDE_FOLDERS`: Folders to exclude from processing
- `EXCLUDE_FILES`: Specific files to exclude
- `OUTPUT_FILE`: Name of the generated documentation file
- `MODEL_ID`: The Claude model ID to use

### 6. Usage

To run SwiftDocsAI:

1. Ensure you're in the project directory and your virtual environment is activated.

2. Run the main script:
   ```
   python main.py
   ```

3. The script will process all files in the specified directory, generate documentation, and save it to the output file (default: `README.md`).

4. Monitor the console and the `logs/process.log` file for progress and any errors.

### 7. API Reference

SwiftDocsAI doesn't expose an API directly, but it uses the AWS Bedrock Runtime API to interact with the Claude AI model. Key functions include:

```python
def invoke_model(metadata, chunk):
    # Invokes the Claude model for a single chunk
    # Returns the response text from the model

def invoke_model_with_retry(metadata, chunk, retries=10, backoff_factor=2):
    # Invokes the model with retry logic in case of failures
    # Returns the response text from the model

def process_in_batches(context_chunks, batch_size, time_window):
    # Processes chunks in batches
    # Returns a list of results from the model
```

These functions are used internally and are not meant to be called directly by users.

### 8. Security Considerations

1. AWS Credentials:
   - Store AWS credentials securely in the `.env` file
   - Do not commit the `.env` file to version control
   - Use IAM roles and temporary credentials when possible

2. File Access:
   - The script reads files from the specified directory
   - Ensure the script has appropriate permissions to read project files
   - Be cautious when processing sensitive files, as their content will be sent to the AI model

3. API Security:
   - Use HTTPS for all API communications (enforced by AWS SDK)
   - Regularly rotate AWS access keys
   - Monitor AWS CloudTrail logs for unauthorized access attempts

4. Output Security:
   - Review generated documentation for any sensitive information before sharing
   - Implement access controls on the generated documentation file

### 9. Monitoring & Logging

SwiftDocsAI uses Python's built-in `logging` module for monitoring and logging:

- Log files are stored in the `logs` directory
- The main log file is `logs/process.log`
- Console output provides real-time progress information

Key metrics to monitor:
- Number of files processed
- Number of chunks created and processed
- API request success rate and latency
- Overall processing time

To analyze logs:
1. Check `logs/process.log` for detailed execution information
2. Use log analysis tools or scripts to parse and visualize log data
3. Monitor for error messages and exceptions

### 10. Troubleshooting

Common issues and solutions:

1. AWS Authentication Errors:
   - Ensure AWS credentials are correctly set in the `.env` file
   - Verify IAM user permissions for AWS Bedrock

2. File Reading Errors:
   - Check file permissions
   - Ensure specified directories and files exist

3. API Rate Limiting:
   - The script implements retry logic with exponential backoff
   - If persistent, increase the `TIME_WINDOW` constant

4. Memory Issues:
   - For large projects, consider processing in smaller batches
   - Increase system memory or use a machine with more RAM

5. Incomplete or Truncated Output:
   - Check `logs/process.log` for any errors during processing
   - Ensure all chunks were successfully processed by the AI model

For additional support, consult the AWS Bedrock documentation or open an issue in the project repository.

### 11. Development Guide

Codebase organization:
- `main.py`: Core script containing all functionality
- `requirements.txt`: Python dependencies
- `.env`: Environment variables (not in version control), refer the `sample.env` to create the `.env` file.

Development environment setup:
1. Follow the installation steps in section 4
2. Use an IDE with Python support (e.g., VSCode, PyCharm)
3. Install development dependencies:
   ```
   pip install black flake8 pytest
   ```

Testing and debugging:
- Add unit tests in a `tests` directory (currently not implemented)
- Use `pytest` to run tests: `pytest tests/`
- For debugging, use your IDE's debugger or add `logging.debug()` statements

Code style:
- Follow PEP 8 guidelines
- Use `black` for code formatting: `black .`
- Use `flake8` for linting: `flake8 .`

### 12. Maintenance & Operations

Regular maintenance tasks:

1. Dependency Updates:
   - Regularly update dependencies in `requirements.txt`
   - Test thoroughly after updates

2. AWS SDK and API Version Updates:
   - Monitor AWS Bedrock API changes
   - Update `boto3` version and adjust code if necessary

3. AI Model Version Updates:
   - Check for new versions of the Claude model
   - Update the `MODEL_ID` constant when new versions are available

4. Log Rotation:
   - Implement log rotation for `logs/process.log`
   - Archive or delete old log files regularly

5. Performance Monitoring:
   - Regularly review processing times and API response times
   - Optimize chunk sizes and batch processing parameters as needed

6. Security Updates:
   - Keep the Python runtime updated
   - Regularly update AWS credentials
   - Review and update IAM policies as needed

Long-term system health:
- Monitor AWS account usage and costs
- Periodically review and optimize the codebase
- Consider containerization (e.g., Docker) for easier deployment and scaling

By following this documentation, users should be able to effectively deploy, use, and maintain the SwiftDocsAI system for automated documentation generation.