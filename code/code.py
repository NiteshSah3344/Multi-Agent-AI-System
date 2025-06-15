# Multi-agent system with API dependencies using Python

import requests

# Base Agent class
class Agent:
    def __init__(self, name):
        self.name = name

    def run(self, data):
        raise NotImplementedError

# PlannerAgent creates a plan based on the user goal
class PlannerAgent(Agent):
    def run(self, goal):
        goal = goal.lower()
        plan = []

        if "launch" in goal:
            plan.append("LaunchAgent")
        if "weather" in goal or "delay" in goal:
            plan.append("WeatherAgent")
            plan.append("NewsAgent")
            plan.append("AnalyzerAgent")
        if "summary" in goal or "summarize" in goal or "delay" in goal:
            plan.append("SummaryAgent")

        if plan:
            return plan
        return []


# LaunchAgent fetches next SpaceX launch info
class LaunchAgent(Agent):
    def run(self, data):
        # Step 1: Get next launch
        response = requests.get("https://api.spacexdata.com/v4/launches/next")
        launch = response.json()
        data["launch_name"] = launch.get("name", "Unknown Launch")

        # Step 2: Get launchpad details using launchpad ID
        launchpad_id = launch.get("launchpad")
        if launchpad_id:
            pad_response = requests.get(f"https://api.spacexdata.com/v4/launchpads/{launchpad_id}")
            pad_data = pad_response.json()
            data["location"] = pad_data.get("locality", "Florida")  # Fallback to "Florida"
        else:
            data["location"] = "Florida"

        return data


# WeatherAgent uses OpenWeatherMap
class WeatherAgent(Agent):
    def __init__(self, name, api_key):
        super().__init__(name)
        self.api_key = api_key

    def run(self, data):
        location = data["location"]
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={self.api_key}"
            response = requests.get(url)
            weather = response.json()
            data["weather_main"] = weather["weather"][0]["main"]
            data["wind_speed"] = weather["wind"]["speed"]
        except Exception as e:
            data["weather_main"] = "Unknown"
            data["wind_speed"] = "N/A"
            print(f"WeatherAgent error: {e}")
        return data


# NewsAgent uses NewsAPI
class NewsAgent(Agent):
    def __init__(self, name, api_key):
        super().__init__(name)
        self.api_key = api_key

    def run(self, data):
        query = data["launch_name"]
        url = f"https://newsapi.org/v2/everything?q={query}&apiKey={self.api_key}"
        response = requests.get(url)
        news = response.json()
        headlines = [article["title"] for article in news.get("articles", [])[:3]]
        data["news_headlines"] = headlines
        return data

# AnalyzerAgent determines if a delay is likely
class AnalyzerAgent(Agent):
    def run(self, data):
        weather_bad = data["weather_main"] in ["Rain", "Thunderstorm", "Snow"]
        news_delay = any("delay" in h.lower() for h in data["news_headlines"])
        data["delay_likely"] = weather_bad or news_delay
        return data

# SummaryAgent formats output
class SummaryAgent(Agent):
    def run(self, data):
        summary = f"Launch: {data.get('launch_name', 'N/A')}\nLocation: {data.get('location', 'N/A')}\n"
        summary += f"Weather: {data.get('weather_main', 'N/A')} (Wind: {data.get('wind_speed', 'N/A')} m/s)\n"
        summary += "News:\n" + "\n".join(f"- {h}" for h in data.get("news_headlines", ["No news found"])) + "\n"
        summary += f"Delay Likely: {'Yes' if data.get('delay_likely') else 'No'}"

        data["summary"] = summary
        return data

# EvaluatorAgent determines if goal is met
class EvaluatorAgent(Agent):
    def run(self, data):
        return "summary" in data

# Coordinator routes data between agents
class Coordinator:
    def __init__(self, agents):
        self.agents = agents

    def execute(self, goal):
        planner = self.agents["PlannerAgent"]
        plan = planner.run(goal)
        data = {"goal": goal}

        for _ in range(3):  # Retry loop
            for agent_name in plan:
                agent = self.agents[agent_name]
                data = agent.run(data)

            evaluator = self.agents["EvaluatorAgent"]
            if evaluator.run(data):
                return data["summary"]
        print(f"Execution Plan: {plan}")

        return "Goal could not be completed after multiple attempts."

# API Keys
OPENWEATHERMAP_KEY = "99e758e0a3ce531579e65377c0443e3d"
NEWSAPI_KEY = "0e56f93f68aa457f9486dd5eb4c8a44d"

# Instantiate agents
agents = {
    "PlannerAgent": PlannerAgent("Planner"),
    "LaunchAgent": LaunchAgent("Launch"),
    "WeatherAgent": WeatherAgent("Weather", OPENWEATHERMAP_KEY),
    "NewsAgent": NewsAgent("News", NEWSAPI_KEY),
    "AnalyzerAgent": AnalyzerAgent("Analyzer"),
    "SummaryAgent": SummaryAgent("Summary"),
    "EvaluatorAgent": EvaluatorAgent("Evaluator"),
}

# Coordinator
coordinator = Coordinator(agents)

# Run example
goal = "Find the next SpaceX launch, check weather at that location, then summarize if it may be delayed."

result = coordinator.execute(goal)
print(result)





