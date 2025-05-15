from dataclasses import dataclass
from pydantic import BaseModel
import random
import httpx

from pydantic_ai import Agent, RunContext


class User(BaseModel):
    name: str


class Result(BaseModel):
    output: bool
    name: str
    dice: str | None = None

def get_agent() -> Agent:
    model = "openai:gpt-4o"
    agent = Agent(
        model=model,
        deps_type=User,  
        output_type=Result,
    )
    return agent


def setup_agent(agent: Agent):
    @agent.system_prompt
    def add_user_name(ctx: RunContext[User]) -> str:  
        return f"The user's name is {ctx.deps.name}."

    @agent.tool
    def check_name(ctx: RunContext[User]) -> Result:
        return Result(output=ctx.deps.name.startswith('A'), name=ctx.deps.name)

    @agent.tool_plain
    def roll_dice() -> str:
        print("Rolling dice")
        return f"Rolled a {random.randint(1, 6)}"


def main():
    agent = get_agent()
    setup_agent(agent)
    # result = agent.run_sync('Does their name start with "A"? Don\'t roll the dice.', deps=User(name='Anne'))
    # result_2 = agent.run_sync('Does their name start with "A"? Don\'t roll the dice.', deps=User(name='Bob'))
    # result_3 = agent.run_sync('Does their name start with "A", Roll the dice.', deps=User(name='Anne'))
    result_4 = agent.run_sync('Does their name start with "A", Roll the dice.', deps=User(name='Bob'))

    # print(result)
    # print(result.output)
    # print(result.usage())

    # print()
    # print(result_2)
    # print(result_2.output)
    # print(result_2.usage())

    # print()
    # print(result_3)
    # print(result_3.output)
    # print(result_3.usage())

    print()
    print(result_4)
    print(result_4.output)
    print(result_4.usage())
    print(result_4.all_messages_json())


########################################################

@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient


agent = Agent(
    model="openai:gpt-4o",
    deps_type=MyDeps,
)

@agent.system_prompt
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:
    response = await ctx.deps.http_client.get(
        'https://example.com#jokes',
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'},
    )
    response.raise_for_status()
    print(response.text)
    return f'Prompt: {response.text}'

async def main_2():
    async with httpx.AsyncClient() as client:
        deps = MyDeps(api_key='foobar', http_client=client)
        result = await agent.run('Tell me a joke?', deps=deps)
        print(result.output)



if __name__ == "__main__":
    import asyncio
    asyncio.run(main_2())
