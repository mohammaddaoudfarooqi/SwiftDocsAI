import os
import json
import logging
from concurrent.futures import ThreadPoolExecutor
import boto3
from botocore.config import Config
from dotenv import load_dotenv
import random
import time

# Directory path
logs_dir = "logs"

# Check if the directory exists
if not os.path.exists(logs_dir):
    # Create the directory
    os.makedirs(logs_dir)
    print(f"Created directory: {logs_dir}")
else:
    print(f"Directory '{logs_dir}' already exists.")
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/process.log"),
        logging.StreamHandler(),  # logging.infos logs to the console
    ],
)

# Log start of script execution
logging.info("Script execution started.")

# Load environment variables from .env file
load_dotenv()
logging.info("Environment variables loaded.")

# Constants for processing with Claude
DEFAULT_MAX_CHARS = 400000
DEFAULT_MAX_WORDS = 90000

CHUNK_LIMIT = 3  # Configurable limit to decide sequential or parallel processing

# Instruction prompt that will be appended to each chunk
INSTRUCTION_PROMPT = """
**Instructions for Generating Comprehensive Technical Documentation**

**Objective:** Create a complete and detailed technical documentation for the provided application. The document should serve as a standalone guide for all users, from beginners to experienced developers, ensuring clarity, organization, and thoroughness throughout.  

**Guidelines for Structure and Content:**  

1. **General Requirements:**  
   - **Standalone Sections:** Each section must be self-contained, including all necessary context to make sense independently. Avoid referencing other sections with phrases like "refer to the section above" or "as mentioned earlier."  
   - **Integration of Context:** Use all available information from the provided context to create exhaustive descriptions for each section.  
   - **Detailed Coverage:** Ensure no detail is omitted. The document should flow logically and provide comprehensive coverage of the application's functionality, architecture, usage, and maintenance.  
   - For every section, integrate all relevant details from the current and previous context to create a standalone and exhaustive description. 

2. **Document Formatting:**  
   - Use **Markdown** syntax for clear formatting.  
   - Include headings, subheadings, bullet points, code blocks, and hyperlinks where appropriate.  
   - Provide code snippets, configuration examples, diagrams, or tables to illustrate concepts.  

3. **Required Sections:**  
   The documentation should follow the structure outlined below:  

   **Title:**  
   `[Project Name] Documentation`  

   **Table of Contents:**  
   List all major sections and subsections with clickable links if applicable.  

   ### 1. Overview  
   - Provide a concise introduction to the project, its purpose, and its key features.  
   - Highlight the problem it solves and its target audience or use cases.  

   ### 2. System Architecture  
   - Describe the high-level architecture, focusing on main components and their interactions.  
   - Include a diagram illustrating the architecture.  

   ### 3. Components  
   - For each major component, describe:  
     - Purpose and core functionality  
     - Technologies used  
     - Interactions with other components  
   - Use diagrams, tables, or charts where helpful.  

   ### 4. Installation & Deployment  
   - Provide step-by-step setup instructions, including:  
     - Prerequisites (e.g., software, hardware)  
     - Environment setup  
     - Deployment commands and scripts  

   ### 5. Configuration  
   - Detail how to configure the system, including:  
     - Environment variables  
     - Configuration files (with examples)  
     - Key settings and their impact  

   ### 6. Usage  
   - Explain how to use the system, including:  
     - API endpoints (if applicable)  
     - Examples of system usage  
     - Instructions for performing common operations  

   ### 7. API Reference  
   - Provide a detailed reference for all available APIs, including:  
     - Endpoint descriptions  
     - Input/output parameters  
     - Example requests and responses  

   ### 8. Security Considerations  
   - Outline security best practices, such as:  
     - Authentication and authorization methods  
     - Data encryption practices  
     - Known vulnerabilities and mitigation strategies  

   ### 9. Monitoring & Logging  
   - Explain how to monitor system performance and access logs, covering:  
     - Key metrics  
     - Tools or dashboards  
     - Log management and analysis  

   ### 10. Troubleshooting  
   - Offer guidance on resolving common issues, including:  
     - Error messages and their meanings  
     - Debugging steps  
     - Links to additional resources or forums  

   ### 11. Development Guide  
   - Provide information for developers working on the project, such as:  
     - Codebase organization and key files  
     - Development environment setup  
     - Testing and debugging procedures  

   ### 12. Maintenance & Operations  
   - Describe ongoing maintenance and operational tasks, including:  
     - Scheduled backups  
     - Regular updates and patches  
     - Monitoring long-term system health  

4. **Examples & Visuals:**  
   - Include **examples** of common scenarios, API calls, and configurations.  
   - Add **visual aids** (e.g., diagrams, charts) to improve understanding.  
   - Ensure examples are realistic and easy to follow.  

5. **Clarity & Accessibility:**  
   - Use simple, precise language and avoid unnecessary jargon.  
   - Make the documentation navigable with proper sectioning and linking.  

The resulting document should be a polished, professional README or technical guide that effectively supports users in deploying, maintaining, and extending the project.
"""

# Calculate the length and word count of the instruction prompt
INSTRUCTION_CHARS = len(INSTRUCTION_PROMPT)
INSTRUCTION_WORDS = len(INSTRUCTION_PROMPT.split())


def process_file(file_path):
    """
    Processes a file by reading its content and splitting it into chunks based on character and word limits.

    Args:
        file_path (str): The path to the file to be processed.

    Returns:
        list: A list of tuples containing metadata and chunk content.
    """
    logging.info(f"Processing file: {file_path}")
    chunks = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.readlines()

        current_chunk = []
        current_chars = 0
        current_words = 0

        for line in content:
            line_words = line.split()
            line_chars = len(line)

            if (
                current_chars + line_chars > DEFAULT_MAX_CHARS - INSTRUCTION_CHARS
                or current_words + len(line_words)
                > DEFAULT_MAX_WORDS - INSTRUCTION_WORDS
            ):
                chunk = "".join(current_chunk)
                metadata = f"### File: {file_path}\n### Chunk: {len(chunks) + 1}\n"
                chunks.append((metadata, chunk))
                current_chunk = []
                current_chars = 0
                current_words = 0

            current_chunk.append(line)
            current_chars += line_chars
            current_words += len(line_words)

        if current_chunk:
            chunk = "".join(current_chunk)
            metadata = f"### File: {file_path}\n### Chunk: {len(chunks) + 1}\n"
            chunks.append((metadata, chunk))

        logging.info(f"File processed: {file_path}, Total chunks: {len(chunks)}")

    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")

    return chunks


def combine_chunks(all_chunks):
    """
    Combines chunks into larger chunks based on character and word limits.

    Args:
        all_chunks (list): A list of tuples containing metadata and chunk content.

    Returns:
        list: A list of combined chunks.
    """
    logging.info("Combining chunks...")
    combined_chunks = []
    current_metadata = []
    current_chunk = []
    current_chars = 0
    current_words = 0

    for metadata, chunk in all_chunks:
        chunk_chars = len(chunk)
        chunk_words = len(chunk.split())

        if current_chars + chunk_chars > (
            DEFAULT_MAX_CHARS - INSTRUCTION_CHARS
        ) or current_words + chunk_words > (DEFAULT_MAX_WORDS - INSTRUCTION_WORDS):
            combined_chunks.append((current_metadata, current_chunk))
            current_metadata = []
            current_chunk = []
            current_chars = 0
            current_words = 0

        current_metadata.append(metadata)
        current_chunk.append(chunk)
        current_chars += chunk_chars
        current_words += chunk_words

    if current_chunk:
        combined_chunks.append((current_metadata, current_chunk))

    logging.info(
        f"Chunks combined into {len(combined_chunks)} chunks to reduce the number of requests."
    )
    return combined_chunks


def combine_results(results):
    """
    Combines results into larger chunks based on character and word limits.

    Args:
        results (list): A list of result strings.

    Returns:
        list: A list of combined results.
    """
    logging.info("Combining results...")
    MAX_CHARS = DEFAULT_MAX_CHARS - INSTRUCTION_CHARS
    MAX_WORDS = DEFAULT_MAX_WORDS - INSTRUCTION_WORDS

    combined = []
    str_combined = ""
    current_chars = 0
    current_words = 0

    for result in results:
        result_chars = len(result)
        result_words = len(result.split())

        if (
            current_chars + result_chars <= MAX_CHARS
            and current_words + result_words <= MAX_WORDS
        ):
            str_combined += result
            current_chars += result_chars
            current_words += result_words
        else:
            combined.append(
                (
                    "Merge these documents into a consolidated single document.",
                    str_combined,
                )
            )
            str_combined = result
            current_chars = result_chars
            current_words = result_words

    if str_combined:
        combined.append(
            ("Merge these documents into a consolidated single document.", str_combined)
        )

    logging.info(f"Results combined into {len(combined)} final combined results.")
    return combined


def read_files_with_chunking(
    directory, file_extensions=None, exclude_folders=None, exclude_files=None
):
    """
    Reads all files in a directory, applies exclusions, and chunks content.

    Args:
        directory (str): The directory to read files from.
        file_extensions (list, optional): List of file extensions to include. Defaults to None.
        exclude_folders (list, optional): List of folders to exclude. Defaults to None.
        exclude_files (list, optional): List of specific files to exclude. Defaults to None.

    Returns:
        tuple: A tuple containing a list of chunks and the processing type.
    """
    logging.info(f"Starting to read files from directory: {directory}")
    exclude_folders = set(exclude_folders or [])
    exclude_files = set(exclude_files or [])
    file_extensions = file_extensions or []

    file_paths = [
        os.path.join(root, file)
        for root, dirs, files in os.walk(directory)
        if not any(folder in root for folder in exclude_folders)
        for file in files
        if (not file_extensions or any(file.endswith(ext) for ext in file_extensions))
        and file not in exclude_files
    ]

    logging.info(f"Total files found: {len(file_paths)}")
    all_chunks = []
    total_chars = 0
    total_words = 0

    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            total_chars += len(content)
            total_words += len(content.split())

    PROCESSING_TYPE = (
        "sequential"
        if total_chars <= (DEFAULT_MAX_CHARS - INSTRUCTION_CHARS) * CHUNK_LIMIT
        and total_words <= (DEFAULT_MAX_WORDS - INSTRUCTION_WORDS) * CHUNK_LIMIT
        else "parallel"
    )

    logging.info(f"Processing mode determined: {PROCESSING_TYPE}")
    if PROCESSING_TYPE == "sequential":
        logging.info("Processing files sequentially...")
        for file_path in file_paths:
            all_chunks.extend(process_file(file_path))
    else:
        logging.info("Processing files in parallel...")
        with ThreadPoolExecutor() as executor:
            results = executor.map(process_file, file_paths)
            for chunks in results:
                all_chunks.extend(chunks)

    logging.info(f"Total chunks created: {len(all_chunks)}")

    # Combine chunks to reduce the number of requests
    combined_chunks = combine_chunks(all_chunks)
    with open("logs/combined_chunks.json", "w") as f:
        json.dump(combined_chunks, f)
    return combined_chunks, PROCESSING_TYPE


def ask_claude_batch(
    context_chunks,
    PROCESSING_TYPE,
    model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
):
    """
    Sends chunks to the Claude model for processing and consolidates the responses.

    Args:
        context_chunks (list): List of context chunks to be processed.
        PROCESSING_TYPE (str): The processing type (sequential or parallel).
        model_id (str, optional): The model ID to use. Defaults to "anthropic.claude-3-5-sonnet-20240620-v1:0".

    Returns:
        str: The final consolidated response.
    """
    client = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
        config=Config(read_timeout=100000),
    )

    def invoke_model(metadata, chunk):
        """
        Invokes the Claude model for a single chunk.

        Args:
            metadata (str): Metadata for the chunk.
            chunk (str): The chunk content.

        Returns:
            str: The response text from the model.
        """
        prompt = f"""
        {INSTRUCTION_PROMPT}

        ### Context:
        {metadata}
        {chunk}
        """
        request_payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 8192,
            "temperature": 0.7,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ],
        }
        response = client.invoke_model(
            modelId=model_id, body=json.dumps(request_payload)
        )
        return json.loads(response["body"].read())["content"][0]["text"]

    # Configuration for batching
    BATCH_SIZE = 8  # Number of requests per batch
    TIME_WINDOW = 60  # Time window in seconds for the batch

    # Function to invoke the model with retry logic
    def invoke_model_with_retry(metadata, chunk, retries=10, backoff_factor=2):
        """
        Invokes the model with retry logic in case of failures.

        Args:
            metadata (str): Metadata for the chunk.
            chunk (str): The chunk content.
            retries (int, optional): Number of retry attempts. Defaults to 10.
            backoff_factor (int, optional): Backoff factor for retry delay. Defaults to 2.

        Returns:
            str: The response text from the model.
        """
        delay = 30  # Initial delay in seconds
        for attempt in range(retries):
            try:
                return invoke_model(metadata, chunk)
            except Exception:
                if attempt < retries - 1:
                    wait_time = delay * (backoff_factor**attempt) + random.uniform(
                        5, 10
                    )
                    logging.info(
                        f"ThrottlingException: Retrying in {wait_time:.2f} seconds..."
                    )
                    time.sleep(wait_time)
                else:
                    logging.info("Maximum retry attempts reached.")
                    raise

    # Function to process chunks in batches
    def process_in_batches(context_chunks, batch_size, time_window):
        """
        Processes chunks in batches.

        Args:
            context_chunks (list): List of context chunks to be processed.
            batch_size (int): Number of requests per batch.
            time_window (int): Time window in seconds for the batch.

        Returns:
            list: List of results from the model.
        """
        results = []
        batch_start = 0
        while batch_start < len(context_chunks):
            batch_end = min(batch_start + batch_size, len(context_chunks))
            batch = context_chunks[batch_start:batch_end]

            logging.info(
                f"Processing batch {batch_start // batch_size + 1} (chunks {batch_start + 1}-{batch_end})..."
            )
            with ThreadPoolExecutor() as executor:
                batch_results = list(
                    executor.map(lambda x: invoke_model_with_retry(*x), batch)
                )
            results.extend(batch_results)

            # Wait for the remainder of the time window if needed
            if batch_end < len(context_chunks):  # Skip delay for the last batch
                time.sleep(time_window)

            batch_start = batch_end

        return results

    # Main logic for processing chunks
    if PROCESSING_TYPE == "parallel":
        logging.info("Processing chunks with Claude in parallel using batching...")

        # Process chunks in batches
        results = process_in_batches(context_chunks, BATCH_SIZE, TIME_WINDOW)

        # Combine chunks to reduce the number of requests
        combined_results = combine_results(results)

        while len(combined_results) != 1:
            # Process results in batches
            results = process_in_batches(combined_results, BATCH_SIZE, TIME_WINDOW)
            # Combine chunks to reduce the number of requests
            combined_results = combine_results(results)

        # Consolidate results into a single document
        final_results = invoke_model_with_retry(
            combined_results[0][0], combined_results[0][1]
        )

        return final_results

    else:
        # Process chunks sequentially and consolidate results
        logging.info("Processing chunks with Claude sequentially...")
        consolidated_context = ""
        final_response = ""
        for metadata, chunk in context_chunks:
            response_text = invoke_model_with_retry(
                "### Previous Context:\n"
                + consolidated_context
                + "\n\n### Current Context:\n"
                + str(metadata),
                str(chunk),
            )
            consolidated_context = response_text

        final_response = consolidated_context
        return final_response


def main(
    directory,
    file_extensions=None,
    exclude_folders=None,
    exclude_files=None,
    output_file="README.md",
    model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
):
    """
    Main function to process all files and save the output.

    Args:
        directory (str): The directory to read files from.
        file_extensions (list, optional): List of file extensions to include. Defaults to None.
        exclude_folders (list, optional): List of folders to exclude. Defaults to None.
        output_file (str, optional): The output file name. Defaults to "README.md".
    """
    logging.info("Starting main process...")
    chunks, PROCESSING_TYPE = read_files_with_chunking(
        directory, file_extensions, exclude_folders, exclude_files
    )

    logging.info("Sending chunks for processing...")
    responses = ask_claude_batch(chunks, PROCESSING_TYPE, model_id)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(responses)

    logging.info(f"Processing complete. Output saved to: {output_file}")


# Entry point for the script
if __name__ == "__main__":
    DIRECTORY = "/Code/SwiftDocsAI"
    FILE_EXTENSIONS = [
        ".ts",
        ".js",
        ".py",
        ".ksh",
        ".yaml",
        ".md",
        "Dockerfile",
        ".yml",
        ".txt",
        ".env",
        ".json",
        ".sh",
        ".html",
    ]  # Use empty list or None to process all file types.
    EXCLUDE_FOLDERS = [".git", ".venv", "node_modules", "logs", "docs"]
    EXCLUDE_FILES = [
        "README.md",
        "LICENSE",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        ".DS_Store",
        ".env",
        ".md",
    ]
    OUTPUT_FILE = "README.md"
    MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"

    try:
        main(
            DIRECTORY,
            FILE_EXTENSIONS,
            EXCLUDE_FOLDERS,
            EXCLUDE_FILES,
            OUTPUT_FILE,
            MODEL_ID,
        )
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise e



