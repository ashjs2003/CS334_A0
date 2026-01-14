from openai import OpenAI
import json
from dataclasses import dataclass
import os
from state import FaithParameters
import dotenv

dotenv_path = "/home/ashjs/vox_city/.env"
dotenv.load_dotenv(dotenv_path)
key = os.getenv("OPENAI_API_KEY")
client = OpenAI()


FAITH_OUTPUT = """teleport_access: {{ "A": boolean, "B": boolean }} or null
spawn_bias: {{ "A": number, "B": number }} or null
location_restriction: {{ "A": [[lon,lat],[lon,lat]] or null, "B": same }} or null
vision_radius: {{ "A": number, "B": number }} or null
inactive_windows: {{ "A": [t1,t2] or null, "B": same }} or null"""


class FaithSystem:
    def __init__(self, narrative: str):
        self.narrative = narrative

        self.system_prompt = f"""
            You are a compiler that converts social or policy narratives
            into simulation parameters.

            You MUST output valid JSON in the format with EXACTLY these keys: {FAITH_OUTPUT}.
            If a parameter is not specified, set it to null.
            Do not explain. Do not add commentary.
        """

        self.user_prompt = f"""
            Simulation context:
            - Two players: A and B
            - Resources spawn across a city (San Fransisco)
            - Transit allows teleportation
            - Parameters affect access, visibility, and mobility

            The way the simulation runs is governed by the following variables: 
            - teleport_access: Boolean (True if player has access to transit, False if player doesn't have access) 
            - spawn_bias: number between 0 and 1 (related to prob that the resource is accessible more towards one player, higher number more chance of resource spawing close) 
            - location_restriction: [(lon1, lat1), (lon2, lat2)] (related to saying that a player cannot go to this 
            specific area defined by the corners of the bounding box) 
            - vision_radius: float (related to the extent to which a player can see if there are resources,
              default is infinite visibility. Minimum is 1000m) 
            - player_inactive_window: [t1, t2] (to say a player cannot move for t1 seconds and after every t2 seconds)

            Narrative:
            \"\"\"
            {self.narrative}
            \"\"\"

            Return JSON with the variables, matching the narrative to the variable and giving an appropriate value.  
        """

    def run(self) -> FaithParameters:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )

        raw_json = response.choices[0].message.content


        data = json.loads(raw_json)

        return FaithParameters(
            teleport_access=data.get("teleport_access"),
            spawn_bias=data.get("spawn_bias"),
            location_restriction=data.get("location_restriction"),
            vision_radius=data.get("vision_radius"),
            inactive_windows=data.get("inactive_windows"),
        )

