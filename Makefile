install:
	python -m pip install -r requirements.txt

run:
	uvicorn app.main:app --reload

seed:
	python -m app.seed

test:
	pytest -q
