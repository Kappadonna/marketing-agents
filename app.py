import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify API keys are set
assert os.getenv("OPENAI_API_KEY"), "Please set OPENAI_API_KEY in .env file"
assert os.getenv("TAVILY_API_KEY"), "Please set TAVILY_API_KEY in .env file"

print("✅ Environment configured successfully")

# Import necessary modules
from agent import create_marketing_campaign_agent, create_campaign_input
from utils import stream_agent, print_campaign_summary, save_campaign_output

print("✅ Imports successful")

# Create the marketing campaign agent
agent = create_marketing_campaign_agent(
    model_name="openai:gpt-4o-mini",  # or "openai:gpt-4o" for better quality
    max_iterations=2,
    performance_threshold=75.0
)

print("✅ Agent system created successfully")

config = {"recursion_limit": 200}

# OPTION A: Basic configuration
campaign_input_neurobuds = create_campaign_input(
    product_info="""
    NeuroBuds Pro – Next-generation wireless earbuds featuring:
    - AI adaptive noise cancellation (blocks 99% of external noise)
    - Focus Mode: audio stimulation to boost concentration (+35% productivity)
    - Real-time translation in 40+ languages
    - Integrated biometric sensors (heart rate, stress level)
    - 48h battery life with wireless charging case
    - Companion app with mental wellness coaching
    - IPX8 waterproof rating
    - 3D spatial audio for full immersion
    Price: €249.99 (early bird: €199.99)
    Certifications: CE, FDA-cleared for health monitoring
    """,
    campaign_goal="Generate pre-orders and build anticipation for the product launch targeting early adopters",
    target_audience="Tech enthusiasts and professionals aged 25–40, remote workers and commuters seeking productivity enhancement, fitness-conscious individuals interested in health tracking, audiophiles who value premium sound quality",
    max_iterations=2,
    performance_threshold=86.0
)

# Aggiungi questi parametri per controllare meglio i costi
if hasattr(campaign_input_neurobuds, '__setitem__'):  # Check if dict-like
    campaign_input_neurobuds["max_searches_per_iteration"] = 3  # Limite ricerche per iterazione
    campaign_input_neurobuds["search_count_current_iteration"] = 0  # Reset contatore
    print("⚙️ Rate limiting enabled: max 3 searches per iteration")

print("✅ Campaign Neurobuds configured: NeuroBuds Pro Smart Earbuds")


async def main(agent, campaign_input_neurobuds, config):
    final_state_neurobuds = await stream_agent(agent, campaign_input_neurobuds, config=config)
    print_campaign_summary(final_state_neurobuds)

    save_campaign_output(final_state_neurobuds, output_dir="campaign_neurobuds")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main(agent, campaign_input_neurobuds, config))