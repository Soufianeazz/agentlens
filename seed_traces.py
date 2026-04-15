"""Demo trace data for the Agent Debugger."""
import asyncio, time, random
import httpx

BASE = "http://localhost:8000"

AGENTS = [
    {
        "name": "research_agent",
        "input": "Research the latest trends in renewable energy for a market report",
        "spans": [
            {"name": "web_search", "type": "retrieval", "input": "renewable energy trends 2024", "output": "Found 12 articles about solar, wind, and battery storage growth...", "dur": 820},
            {"name": "llm_summarize", "type": "llm", "model": "gpt-4o", "input": "Summarize these articles...", "output": "Solar capacity grew 45% YoY. Battery costs down 30%. Wind offshore expanding rapidly.", "dur": 2100, "tokens": 1200, "cost": 0.009},
            {"name": "fact_check", "type": "tool", "input": "Verify statistics", "output": "All facts verified against 3 sources", "dur": 430},
            {"name": "llm_report", "type": "llm", "model": "gpt-4o", "input": "Write a market report section...", "output": "The renewable energy sector is experiencing unprecedented growth...", "dur": 3400, "tokens": 2800, "cost": 0.021},
        ],
        "output": "Market report section completed with verified statistics",
        "status": "completed",
    },
    {
        "name": "booking_flow",
        "input": "Book a flight from Berlin to Paris for next Friday, business class",
        "spans": [
            {"name": "parse_intent", "type": "llm", "model": "gpt-4o-mini", "input": "Extract flight params", "output": '{"from": "BER", "to": "CDG", "class": "business"}', "dur": 380, "tokens": 210, "cost": 0.00006},
            {"name": "search_flights", "type": "tool", "input": "BER->CDG business", "output": "3 flights found: LH1234 08:00 EUR890, AF5678 11:30 EUR750, LH9012 16:00 EUR920", "dur": 1200},
            {"name": "rank_options", "type": "decision", "input": "Rank by price/time tradeoff", "output": "Recommended: AF5678 (best value)", "dur": 150},
            {"name": "confirm_booking", "type": "tool", "input": "Book AF5678 for user_123", "output": "Booking confirmed. Reference: AF-2024-78901", "dur": 890},
        ],
        "output": "Flight booked: AF5678 Berlin-Paris Friday 11:30, Business. Ref: AF-2024-78901",
        "status": "completed",
    },
    {
        "name": "support_agent",
        "input": "Customer says their account is locked and they cant log in",
        "spans": [
            {"name": "classify_issue", "type": "llm", "model": "claude-3-haiku", "input": "Classify: account locked", "output": "Category: authentication_issue, Priority: high", "dur": 290, "tokens": 180, "cost": 0.000072},
            {"name": "lookup_account", "type": "tool", "input": "Find account by email", "output": "Account found: locked, reason: 5 failed attempts", "dur": 340},
            {"name": "generate_response", "type": "llm", "model": "claude-3-haiku", "input": "Write support response for locked account", "output": "Hi! I can see your account was locked after multiple failed login attempts. I have unlocked it now.", "dur": 580, "tokens": 420, "cost": 0.000168},
            {"name": "unlock_account", "type": "tool", "input": "Unlock account user@example.com", "output": "Account unlocked successfully", "dur": 120},
        ],
        "output": "Account unlocked. Customer notified with personalized response.",
        "status": "completed",
    },
    {
        "name": "data_pipeline",
        "input": "Process and analyze sales data from Q4 CSV export",
        "spans": [
            {"name": "load_csv", "type": "tool", "input": "Load q4_sales.csv", "output": "2847 rows loaded, 12 columns", "dur": 230},
            {"name": "validate_schema", "type": "decision", "input": "Check required columns exist", "output": "Schema valid: date, product, revenue, region all present", "dur": 80},
            {"name": "llm_anomaly_detect", "type": "llm", "model": "gpt-4o", "input": "Identify anomalies in this dataset...", "output": "ERROR: Context length exceeded.", "dur": 4100, "tokens": 8000, "cost": 0.06, "status": "failed", "error": "Context length exceeded - chunk data before sending to LLM"},
        ],
        "output": None,
        "status": "failed",
        "error": "LLM context limit exceeded at anomaly detection step",
    },
    {
        "name": "content_generator",
        "input": "Generate 5 LinkedIn posts about our new AI product launch",
        "spans": [
            {"name": "brand_check", "type": "retrieval", "input": "Load brand guidelines", "output": "Tone: professional but approachable. Avoid: hype words.", "dur": 110},
            {"name": "generate_drafts", "type": "llm", "model": "gpt-4o", "input": "Write 5 LinkedIn posts for AI launch...", "output": "Post 1: We built something...\nPost 2: The future of work...\n(5 drafts)", "dur": 5200, "tokens": 3100, "cost": 0.0232},
            {"name": "tone_check", "type": "llm", "model": "gpt-4o-mini", "input": "Check tone compliance for 5 posts", "output": "Posts 1,2,4,5 pass. Post 3 too salesy - revised.", "dur": 1100, "tokens": 890, "cost": 0.000267},
            {"name": "schedule_posts", "type": "tool", "input": "Schedule 5 posts across next 2 weeks", "output": "Scheduled: Mon/Wed/Fri/Mon/Wed at 9am CET", "dur": 200},
        ],
        "output": "5 LinkedIn posts generated, tone-checked, and scheduled",
        "status": "completed",
    },
]


async def seed():
    async with httpx.AsyncClient() as c:
        for agent in AGENTS:
            r = await c.post(f"{BASE}/traces", json={"name": agent["name"], "input": agent["input"]})
            tid = r.json()["trace_id"]

            for sp in agent["spans"]:
                r2 = await c.post(f"{BASE}/traces/{tid}/spans", json={
                    "name": sp["name"],
                    "span_type": sp["type"],
                    "input": sp.get("input"),
                    "model": sp.get("model"),
                })
                sid = r2.json()["span_id"]
                await c.post(f"{BASE}/traces/{tid}/spans/{sid}/end", json={
                    "status": sp.get("status", "completed"),
                    "output": sp.get("output"),
                    "error": sp.get("error"),
                    "tokens": sp.get("tokens"),
                    "cost_usd": sp.get("cost"),
                })

            await c.post(f"{BASE}/traces/{tid}/end", json={
                "status": agent["status"],
                "output": agent.get("output"),
                "error": agent.get("error"),
            })
            print(f"  OK {agent['name']} ({agent['status']}) - {len(agent['spans'])} spans")

    print("\nDone. Open http://localhost:8000/traces.html")


if __name__ == "__main__":
    asyncio.run(seed())
