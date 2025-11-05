import asyncio
import aiohttp
import json
import time
from pathlib import Path
import os


async def test_memo_generation():
    """Test the memo generation API using Zinnia mock data and YAML template"""

    base_url = "http://localhost:8000"

    print("VC Memo API Test Script - Using Zinnia Mock Data")
    print("=" * 50)

    # Get the project root directory (vc-memo-backend)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    mock_data_dir = project_root / "mock-data" / "zinnia"
    template_path = project_root / "template_standard.yaml"

    # Verify files exist
    if not mock_data_dir.exists():
        print(f"Error: Mock data directory not found: {mock_data_dir}")
        return

    if not template_path.exists():
        print(f"Error: Template file not found: {template_path}")
        return

    # List of files to upload from mock-data/zinnia
    zinnia_files = [
        "5.23  Zinnia Investor Deck.pdf",
        "Email Chains.docx",
        "Financials.xlsx",
        "Zinnia Mock Diligence.docx",
    ]

    print(f"\n1. Loading files from: {mock_data_dir}")
    print(f"   Template file: {template_path}")

    # Verify all files exist
    missing_files = []
    for filename in zinnia_files:
        file_path = mock_data_dir / filename
        if not file_path.exists():
            missing_files.append(filename)
        else:
            print(f"   ✓ Found: {filename}")

    if missing_files:
        print(f"\nError: Missing files: {', '.join(missing_files)}")
        return

    # Determine content types for files
    def get_content_type(filename: str) -> str:
        ext = filename.split(".")[-1].lower()
        content_types = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "yaml": "application/x-yaml",
            "yml": "application/x-yaml",
        }
        return content_types.get(ext, "application/octet-stream")

    # Now test the API
    async with aiohttp.ClientSession() as session:
        # 1. Upload files with template
        print("\n" + "=" * 50)
        print("TESTING MEMO GENERATION WITH ZINNIA MOCK DATA")
        print("=" * 50)
        print("1. Uploading documents and YAML template...")

        data = aiohttp.FormData()
        data.add_field("company_name", "Zinnia")
        data.add_field(
            "funding_stage", "Series A"
        )  # Will be extracted from documents if different

        # Add all Zinnia files
        for filename in zinnia_files:
            file_path = mock_data_dir / filename
            with open(file_path, "rb") as f:
                content_type = get_content_type(filename)
                data.add_field(
                    "files",
                    f.read(),
                    filename=filename,
                    content_type=content_type,
                )
            print(f"   ✓ Added: {filename}")

        # Add YAML template file
        with open(template_path, "rb") as f:
            data.add_field(
                "template_file",
                f.read(),
                filename=template_path.name,
                content_type="application/x-yaml",
            )
        print(f"   ✓ Added template: {template_path.name}")

        async with session.post(f"{base_url}/upload-and-process", data=data) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                print(f"Error uploading files: HTTP {resp.status} - {error_text}")
                return

            result = await resp.json()
            if "job_id" not in result:
                print(f"Unexpected upload response: {result}")
                return

            print(f"Upload response: {json.dumps(result, indent=2)}")
            job_id = result["job_id"]

        # 2. Poll for status
        print(f"\n2. Polling job status for job_id: {job_id}")

        status = "processing"
        attempts = 0
        max_attempts = 60  # 5 minutes timeout

        while status == "processing" and attempts < max_attempts:
            await asyncio.sleep(5)  # Wait 5 seconds between polls

            async with session.get(f"{base_url}/status/{job_id}") as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    print(f"Error checking status: HTTP {resp.status} - {error_text}")
                    status = "failed"
                    break

                status_result = await resp.json()
                if "status" not in status_result:
                    print(f"Unexpected response format: {status_result}")
                    status = "failed"
                    break

                status = status_result["status"]
                progress = status_result.get("progress", "")
                print(f"Status: {status} - {progress}")

            attempts += 1

        # 3. Get the memo
        if status == "completed":
            print(f"\n3. Retrieving completed memo...")

            try:
                async with session.get(f"{base_url}/memo/{job_id}") as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        print(
                            f"Error retrieving memo: HTTP {resp.status} - {error_text}"
                        )
                    else:
                        memo_result = await resp.json()

                        print("\n" + "=" * 70)
                        print("GENERATED MEMO")
                        print("=" * 70)
                        if "memo_content" in memo_result:
                            print(memo_result["memo_content"])
                        else:
                            print("Memo content not found in response")
                            print(f"Response: {json.dumps(memo_result, indent=2)}")

                        if "confidence_scores" in memo_result:
                            print("\n" + "=" * 70)
                            print("CONFIDENCE SCORES")
                            print("=" * 70)
                            for section, score in memo_result[
                                "confidence_scores"
                            ].items():
                                print(f"{section}: {score:.2f}")

                        if "flagged_items" in memo_result:
                            print("\n" + "=" * 70)
                            print(
                                f"FLAGGED ITEMS ({len(memo_result['flagged_items'])})"
                            )
                            print("=" * 70)
                            for item in memo_result["flagged_items"]:
                                print(f"- {item['section']}: {item['reason']}")
                                if item.get("missing_data"):
                                    print(
                                        f"  Missing: {', '.join(item['missing_data'])}"
                                    )
            except Exception as e:
                print(f"Exception while retrieving memo: {e}")

        elif status == "failed":
            print(f"\n3. Job failed!")
            try:
                async with session.get(f"{base_url}/status/{job_id}") as resp:
                    if resp.status == 200:
                        error_result = await resp.json()
                        error_msg = error_result.get("error", "Unknown error")
                        if isinstance(error_msg, list):
                            error_msg = "; ".join(str(e) for e in error_msg)
                        print(f"Error: {error_msg}")
                    else:
                        error_text = await resp.text()
                        print(
                            f"Error retrieving status: HTTP {resp.status} - {error_text}"
                        )
            except Exception as e:
                print(f"Exception while checking error status: {e}")

        else:
            print(f"\n3. Job timed out (status: {status})")


async def test_health_check():
    """Test the health endpoint"""
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/health") as resp:
            result = await resp.json()
            print(f"Health check: {result}")


if __name__ == "__main__":
    asyncio.run(test_memo_generation())
