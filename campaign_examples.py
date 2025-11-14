"""
Campaign Configuration Examples
================================

Pre-configured campaign templates for quick testing and demonstration.
Use these in the Streamlit sidebar to quickly set up different campaign types.
"""

# ============================================================================
# TECH PRODUCT CAMPAIGNS
# ============================================================================

NEUROBUDS_PRO = {
    "product_name": "NeuroBuds Pro",
    "product_info": """Next-generation wireless earbuds featuring:
- AI adaptive noise cancellation (blocks 99% of external noise)
- Focus Mode: audio stimulation to boost concentration (+35% productivity)
- Real-time translation in 40+ languages
- Integrated biometric sensors (heart rate, stress level)
- 48h battery life with wireless charging case
- Companion app with mental wellness coaching
- IPX8 waterproof rating
- 3D spatial audio for full immersion
Price: €249.99 (early bird: €199.99)
Certifications: CE, FDA-cleared for health monitoring""",
    "campaign_goal": "Generate pre-orders and build anticipation for the product launch targeting early adopters and tech enthusiasts",
    "target_audience": "Tech enthusiasts and professionals aged 25-40, remote workers and commuters seeking productivity enhancement, fitness-conscious individuals interested in health tracking, audiophiles who value premium sound quality",
    "max_iterations": 2,
    "performance_threshold": 75.0
}

SMART_WATER_BOTTLE = {
    "product_name": "HydroTrack Pro",
    "product_info": """Revolutionary smart water bottle that:
- Tracks daily hydration goals with LED indicators
- Self-cleaning UV-C technology
- Keeps drinks cold for 24h, hot for 12h
- Eco-friendly materials (BPA-free, recyclable)
- Integrates with fitness apps (Apple Health, Google Fit, Strava)
- Personalized hydration reminders based on activity
- Built-in water quality sensor
- Wireless charging base included
Price: $79.99
Capacity: 750ml""",
    "campaign_goal": "Drive awareness and early adoption among health-conscious professionals and fitness enthusiasts",
    "target_audience": "Health-conscious professionals aged 25-45, gym-goers and fitness enthusiasts, office workers who forget to drink water, eco-conscious consumers looking for sustainable products",
    "max_iterations": 3,
    "performance_threshold": 70.0
}

AI_PRODUCTIVITY_APP = {
    "product_name": "FlowMaster AI",
    "product_info": """AI-powered productivity platform that:
- Intelligent task prioritization using machine learning
- Automatic meeting summarization and action items
- Deep work sessions with distraction blocking
- Team collaboration with async communication
- Integration with 100+ tools (Slack, Notion, Gmail, etc.)
- Personalized productivity insights and recommendations
- Voice-to-task natural language processing
- Cross-platform: Web, iOS, Android, Desktop
Pricing: Free tier, Pro at $12/month, Team at $25/user/month
Free trial: 30 days""",
    "campaign_goal": "Acquire 10,000+ sign-ups for the free trial and convert 20% to paid plans within 90 days",
    "target_audience": "Knowledge workers and professionals aged 25-45, startup founders and entrepreneurs, remote teams and distributed companies, productivity-focused individuals who use multiple tools daily",
    "max_iterations": 3,
    "performance_threshold": 80.0
}

# ============================================================================
# HEALTH & WELLNESS CAMPAIGNS
# ============================================================================

MEDITATION_APP = {
    "product_name": "MindFlow",
    "product_info": """Personalized meditation and mindfulness app featuring:
- AI-guided meditation sessions (5-60 minutes)
- Sleep stories narrated by calming voices
- Breathing exercises for stress relief
- Progress tracking and streak rewards
- Community challenges and group sessions
- Offline mode for meditation anywhere
- Integration with wearables (Apple Watch, Fitbit)
- Personalized recommendations based on mood and goals
Pricing: Free with ads, Premium at $9.99/month or $59.99/year
30-day free trial for Premium""",
    "campaign_goal": "Increase app downloads and Premium subscriptions among stressed professionals seeking mental wellness solutions",
    "target_audience": "Stressed professionals aged 25-50, beginners to meditation seeking guidance, people with sleep issues, individuals interested in mindfulness and mental health",
    "max_iterations": 2,
    "performance_threshold": 65.0
}

NUTRITION_TRACKING = {
    "product_name": "NutriScan AI",
    "product_info": """Revolutionary nutrition app with AI food recognition:
- Scan any food with camera for instant nutrition facts
- Barcode scanning for packaged foods
- Personalized meal plans based on goals and dietary restrictions
- Macro and calorie tracking with intelligent insights
- Recipe database with 50,000+ healthy recipes
- Integration with fitness apps and wearables
- Water intake tracking and reminders
- Supplement tracking and recommendations
Pricing: Free basic, Premium at $14.99/month (includes AI meal planning)
14-day free trial""",
    "campaign_goal": "Drive app downloads and Premium conversions among health-conscious individuals and fitness enthusiasts",
    "target_audience": "Fitness enthusiasts and gym-goers aged 20-40, people trying to lose/gain weight, athletes and bodybuilders tracking macros, individuals with dietary restrictions (vegan, keto, etc.)",
    "max_iterations": 2,
    "performance_threshold": 70.0
}

# ============================================================================
# B2B SAAS CAMPAIGNS
# ============================================================================

PROJECT_MANAGEMENT_TOOL = {
    "product_name": "TeamSync Pro",
    "product_info": """All-in-one project management platform for modern teams:
- Visual project planning with Gantt charts and Kanban boards
- Time tracking and resource allocation
- Real-time collaboration and commenting
- Automated workflows and custom integrations
- Advanced reporting and analytics dashboard
- Client portal for external stakeholders
- Mobile apps (iOS & Android)
- Security: SOC 2 Type II, GDPR compliant
Pricing: Starter $15/user/month, Business $29/user/month, Enterprise (custom)
14-day free trial, no credit card required""",
    "campaign_goal": "Generate qualified leads from SMBs and convert to paying customers with focus on annual plans",
    "target_audience": "Project managers and team leads in companies with 10-200 employees, agencies and consulting firms, remote-first companies, teams struggling with fragmented tools",
    "max_iterations": 3,
    "performance_threshold": 75.0
}

CUSTOMER_SUPPORT_AI = {
    "product_name": "SupportGenius AI",
    "product_info": """AI-powered customer support automation platform:
- Intelligent chatbot that learns from your knowledge base
- Automated ticket routing and prioritization
- Sentiment analysis and customer satisfaction tracking
- Multi-channel support (email, chat, social media, SMS)
- Integration with CRM and helpdesk tools
- Real-time agent assist with AI suggestions
- Comprehensive analytics and reporting
- Multilingual support (50+ languages)
Pricing: Growth $99/month, Business $299/month, Enterprise (custom)
ROI: Average 40% reduction in support costs
30-day free trial""",
    "campaign_goal": "Position as the leading AI support solution and generate 500+ qualified demo requests from B2B companies",
    "target_audience": "Customer support managers in SaaS companies, E-commerce businesses with high ticket volume, startups scaling their support operations, companies looking to reduce support costs",
    "max_iterations": 3,
    "performance_threshold": 80.0
}

# ============================================================================
# E-COMMERCE & CONSUMER GOODS
# ============================================================================

SUSTAINABLE_FASHION = {
    "product_name": "EcoThreads Collection",
    "product_info": """Sustainable fashion brand with eco-friendly materials:
- 100% organic cotton and recycled fabrics
- Carbon-neutral shipping
- Fair trade certified production
- Timeless designs that last for years
- Transparent supply chain with blockchain tracking
- Plastic-free packaging
- Tree planted for every order
- Gender-neutral sizing
Price range: $35-$150 per item
Collections: Basics, Activewear, Workwear, Accessories""",
    "campaign_goal": "Launch new collection and drive online sales while building brand awareness among eco-conscious millennials and Gen Z",
    "target_audience": "Eco-conscious consumers aged 20-40, millennials and Gen Z interested in sustainable living, fashion-forward individuals seeking ethical alternatives, professionals wanting sustainable workwear",
    "max_iterations": 2,
    "performance_threshold": 70.0
}

GOURMET_COFFEE = {
    "product_name": "Origins Coffee Roasters",
    "product_info": """Premium single-origin coffee subscription service:
- Freshly roasted beans from sustainable farms
- Monthly subscription with curated selection
- Direct trade relationships with farmers
- Tasting notes and brewing guides included
- Customizable roast levels and grind options
- Carbon-neutral delivery
- Exclusive access to rare micro-lots
- Barista tips and recipes
Pricing: Discovery box $29/month, Premium $45/month, Ultimate $65/month
One-time purchases available, free shipping on subscriptions
First month 20% off with code ORIGINS20""",
    "campaign_goal": "Acquire 1,000 new subscribers and increase brand awareness among coffee enthusiasts and professionals",
    "target_audience": "Coffee enthusiasts and connoisseurs aged 25-50, remote workers who drink multiple cups daily, gift-givers looking for premium subscriptions, people interested in ethical sourcing and sustainability",
    "max_iterations": 2,
    "performance_threshold": 65.0
}

# ============================================================================
# EDUCATION & ONLINE LEARNING
# ============================================================================

CODING_BOOTCAMP = {
    "product_name": "CodeMaster Academy",
    "product_info": """Intensive online coding bootcamp with job guarantee:
- 12-week full-stack web development program
- Live instruction with experienced developers
- 1-on-1 mentorship and career coaching
- Real-world projects for portfolio
- Job placement assistance and interview prep
- Flexible payment options (upfront, monthly, ISA)
- Lifetime access to course materials
- Alumni network and community
Tech stack: JavaScript, React, Node.js, Python, SQL
Pricing: $12,000 (ISA available: pay after you get a job)
Job placement rate: 94% within 6 months""",
    "campaign_goal": "Enroll 100 students for next cohort and position as the top-choice coding bootcamp for career changers",
    "target_audience": "Career changers aged 25-40 looking to break into tech, recent graduates seeking practical skills, professionals in declining industries, people seeking remote work opportunities",
    "max_iterations": 3,
    "performance_threshold": 80.0
}

LANGUAGE_LEARNING_APP = {
    "product_name": "LinguaFlow",
    "product_info": """AI-powered language learning platform with immersive approach:
- Conversational AI tutors for 30+ languages
- Speech recognition for pronunciation practice
- Personalized learning paths based on goals
- Real-world content (news, podcasts, videos)
- Spaced repetition algorithm for vocabulary
- Live group lessons with native speakers
- Gamification with challenges and achievements
- Offline mode for learning on-the-go
Pricing: Free basic, Premium $12.99/month or $79.99/year
7-day free trial for Premium
Most popular languages: Spanish, French, German, Japanese, Korean, Mandarin""",
    "campaign_goal": "Grow user base to 1 million active learners and increase Premium conversion rate to 15%",
    "target_audience": "Aspiring polyglots and language enthusiasts aged 18-45, travelers preparing for trips abroad, professionals needing language skills for work, students supplementing formal language education",
    "max_iterations": 2,
    "performance_threshold": 70.0
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_all_campaigns():
    """Get list of all campaign names"""
    return [
        "NeuroBuds Pro (Tech)",
        "HydroTrack Pro (Health Tech)",
        "FlowMaster AI (Productivity)",
        "MindFlow (Wellness)",
        "NutriScan AI (Health)",
        "TeamSync Pro (B2B SaaS)",
        "SupportGenius AI (B2B)",
        "EcoThreads (Fashion)",
        "Origins Coffee (E-commerce)",
        "CodeMaster Academy (Education)",
        "LinguaFlow (EdTech)"
    ]

def get_campaign_config(campaign_name: str) -> dict:
    """Get configuration for a specific campaign"""
    campaigns = {
        "NeuroBuds Pro (Tech)": NEUROBUDS_PRO,
        "HydroTrack Pro (Health Tech)": SMART_WATER_BOTTLE,
        "FlowMaster AI (Productivity)": AI_PRODUCTIVITY_APP,
        "MindFlow (Wellness)": MEDITATION_APP,
        "NutriScan AI (Health)": NUTRITION_TRACKING,
        "TeamSync Pro (B2B SaaS)": PROJECT_MANAGEMENT_TOOL,
        "SupportGenius AI (B2B)": CUSTOMER_SUPPORT_AI,
        "EcoThreads (Fashion)": SUSTAINABLE_FASHION,
        "Origins Coffee (E-commerce)": GOURMET_COFFEE,
        "CodeMaster Academy (Education)": CODING_BOOTCAMP,
        "LinguaFlow (EdTech)": LANGUAGE_LEARNING_APP
    }
    
    return campaigns.get(campaign_name, NEUROBUDS_PRO)

# ============================================================================
# CAMPAIGN CATEGORIES
# ============================================================================

CATEGORIES = {
    "Tech & Gadgets": [
        "NeuroBuds Pro (Tech)",
        "HydroTrack Pro (Health Tech)",
        "FlowMaster AI (Productivity)"
    ],
    "Health & Wellness": [
        "MindFlow (Wellness)",
        "NutriScan AI (Health)"
    ],
    "B2B SaaS": [
        "TeamSync Pro (B2B SaaS)",
        "SupportGenius AI (B2B)"
    ],
    "E-commerce": [
        "EcoThreads (Fashion)",
        "Origins Coffee (E-commerce)"
    ],
    "Education": [
        "CodeMaster Academy (Education)",
        "LinguaFlow (EdTech)"
    ]
}

def get_campaigns_by_category(category: str) -> list:
    """Get all campaigns in a specific category"""
    return CATEGORIES.get(category, [])
