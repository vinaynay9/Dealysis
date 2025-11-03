import asyncio
import aiohttp
import json
import time
from pathlib import Path
import os
from datetime import datetime


async def test_optimized_memo_generation():
    """Test the optimized memo generation API with cost tracking"""

    base_url = "https://dealysis.onrender.com"

    print("VC Memo API Test Script - OPTIMIZED PIPELINE")
    print("=" * 50)

    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    mock_data_dir = script_dir / "mock-data" / "zinnia"
    template_path = script_dir / "template_standard.yaml"

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
    total_file_size = 0
    for filename in zinnia_files:
        file_path = mock_data_dir / filename
        if not file_path.exists():
            missing_files.append(filename)
        else:
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            total_file_size += file_size
            print(f"   ✓ Found: {filename} ({file_size:.1f} MB)")

    if missing_files:
        print(f"\nError: Missing files: {', '.join(missing_files)}")
        return

    print(f"\nTotal file size: {total_file_size:.1f} MB")

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

    # Test the optimized API
    async with aiohttp.ClientSession() as session:
        # 1. Upload files with template
        print("\n" + "=" * 70)
        print("TESTING OPTIMIZED MEMO GENERATION WITH ZINNIA MOCK DATA")
        print("=" * 70)
        print("1. Uploading documents and YAML template...")

        start_upload_time = time.time()

        data = aiohttp.FormData()
        data.add_field("company_name", "Zinnia")
        data.add_field("funding_stage", "Series A")

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

            print(f"\nUpload response: {json.dumps(result, indent=2)}")
            job_id = result["job_id"]

        upload_time = time.time() - start_upload_time
        print(f"Upload completed in {upload_time:.1f} seconds")

        # 2. Poll for status
        print(f"\n2. Polling job status for job_id: {job_id}")

        start_processing_time = time.time()
        status = "processing"
        attempts = 0
        max_attempts = 120  # 10 minutes timeout (5s intervals)
        last_progress = ""

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

                # Only print if progress changed
                if progress != last_progress:
                    elapsed = time.time() - start_processing_time
                    print(f"[{elapsed:>6.1f}s] Status: {status} - {progress}")
                    last_progress = progress

            attempts += 1

        processing_time = time.time() - start_processing_time
        total_time = upload_time + processing_time

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
                        print("GENERATED MEMO (first 1000 chars)")
                        print("=" * 70)
                        if "memo_content" in memo_result:
                            print(memo_result["memo_content"][:1000] + "...")
                            print(
                                f"\nTotal memo length: {len(memo_result['memo_content'])} characters"
                            )

                            # Export memo to file
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            output_dir = script_dir / "exported_memos"
                            output_dir.mkdir(exist_ok=True)

                            memo_filename = output_dir / f"memo_zinnia_{timestamp}.md"
                            with open(memo_filename, "w", encoding="utf-8") as f:
                                f.write("# Investment Memo: Zinnia\n\n")
                                f.write(f"Generated: {datetime.now().isoformat()}\n")
                                f.write(f"Job ID: {job_id}\n")
                                f.write(f"Company: Zinnia\n")
                                f.write(f"Funding Stage: Series A\n\n")
                                f.write("---\n\n")
                                f.write(memo_result["memo_content"])

                                # Add metadata at the end
                                f.write("\n\n---\n\n## Metadata\n\n")

                                if "confidence_scores" in memo_result:
                                    f.write("### Confidence Scores\n\n")
                                    for section, score in memo_result[
                                        "confidence_scores"
                                    ].items():
                                        f.write(f"- **{section}**: {score:.2f}\n")
                                    f.write("\n")

                                if "flagged_items" in memo_result:
                                    f.write("### Flagged Items\n\n")
                                    for item in memo_result["flagged_items"]:
                                        f.write(
                                            f"- **{item['section']}**: {item['reason']}\n"
                                        )
                                        if item.get("missing_data"):
                                            f.write(
                                                f"  - Missing: {', '.join(item['missing_data'])}\n"
                                            )
                                    f.write("\n")

                            print(f"\n✓ Memo exported to: {memo_filename}")
                        else:
                            print("Memo content not found in response")

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

                # Check for performance metrics
                async with session.get(f"{base_url}/status/{job_id}") as resp:
                    if resp.status == 200:
                        final_status = await resp.json()

                        print("\n" + "=" * 70)
                        print("PERFORMANCE METRICS")
                        print("=" * 70)
                        print(f"Total processing time: {total_time:.1f} seconds")
                        print(f"  - Upload time: {upload_time:.1f}s")
                        print(f"  - Pipeline time: {processing_time:.1f}s")

                        if "performance" in final_status:
                            perf = final_status["performance"]
                            print(f"\nPipeline Performance:")
                            print(
                                f"  - Total cost: ${perf.get('total_cost_usd', 0):.4f}"
                            )
                            print(
                                f"  - Chunks processed: {perf.get('chunks_processed', 0)}"
                            )
                            print(f"  - Cache hits: {perf.get('cache_hits', 0)}")

                            # Cost analysis
                            print(f"\n💰 COST ANALYSIS:")
                            cost = perf.get("total_cost_usd", 0)
                            if cost < 0.25:
                                print(
                                    f"  ✅ SUCCESS: Cost ${cost:.4f} is under target of $0.25"
                                )
                            else:
                                print(
                                    f"  ⚠️  WARNING: Cost ${cost:.4f} exceeds target of $0.25"
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
            except Exception as e:
                print(f"Exception while checking error status: {e}")

        else:
            print(f"\n3. Job timed out (status: {status})")

        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total time: {total_time:.1f} seconds")
        print(f"Final status: {status}")


async def test_health_check():
    """Test the health endpoint"""
    async with aiohttp.ClientSession() as session:
        async with session.get("https://dealysis.onrender.com/health") as resp:
            result = await resp.json()
            print(f"Health check: {result}")


if __name__ == "__main__":
    print(f"Starting optimized pipeline test at {datetime.now().isoformat()}")
    asyncio.run(test_optimized_memo_generation())
