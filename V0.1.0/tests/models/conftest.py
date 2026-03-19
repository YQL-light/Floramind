import pytest
from tortoise import Tortoise
from app.models.user import User 
from app.models.plant import Plant
from app.core.security import get_password_hash 

@pytest.fixture(scope="function")
async def db_setup_and_teardown():
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["app.models.user", "app.models.plant"]}, 
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()

@pytest.fixture(scope="function")
async def create_user(request, db_setup_and_teardown): 
    unique_suffix = request.node.name.replace("/", "_").replace("[", "_").replace("]", "_")
    MAX_USERNAME_LEN = 50
    required_prefix = "fixture_user_" 
    max_suffix_len = MAX_USERNAME_LEN - len(required_prefix) 
    truncated_suffix = unique_suffix[:max_suffix_len]
    username = f"{required_prefix}{truncated_suffix}" 
    email = f"{username}@test.com"
    
    try:
        password_hash = get_password_hash("testpassword123")
    except NameError:
        password_hash = "dummy_hashed_password" 

    user = await User.create(
        username=username,
        email=email,
        password=password_hash,
    )
    return user

@pytest.fixture(scope="function")
async def create_plant(create_user):
    user = create_user
    plant = await Plant.create(
        user=user,
        nickname="UniquePlantNick",
        species="UniquePlantSpecies",
        water_cycle=10,
        fertilize_cycle=40,
    )
    return plant