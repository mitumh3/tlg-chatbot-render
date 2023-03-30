init:
	black src/*.py --line-length=120
	isort src/*.py --line-length=120
	black src/**/*.py --line-length=120
	isort src/**/*.py --line-length=120