SHELL := /bin/bash 

build_a11y_scan:
	cd lambdas/a11y_scan; \
	if [[ ! -d node_modules ]]; \
	then \
		echo "Installing pa11y deps"; \
		npm install && rm -rf node_modules/puppeteer && \
			sed -i '' "10s/require('puppeteer')/require('puppeteer-core')/" node_modules/pa11y/lib/pa11y.js; \
	fi; \

	cd ..; \

	if [[ ! -f lambdas/chrome_aws_lambda.zip ]]; \
	then \
		git clone --depth=1 https://github.com/alixaxel/chrome-aws-lambda.git && \
		cd chrome-aws-lambda && \
		make chrome_aws_lambda.zip && \
		mv chrome_aws_lambda.zip ../lambdas/chrome_aws_lambda.zip && \
		cd .. && \
		rm -rf chrome-aws-lambda/; \
	fi; \

	echo "All done making a11y_scan lambda"

	
build_results_joiner:
	
	# make tmp dir and copy lambda contents to it
	mkdir tmp
	rsync -av --exclude __pycache__ --progress lambdas/results_joiner/ tmp/

	# install deps
	pip install -r tmp/requirements.txt -t tmp/

	# zip it all up
	mkdir lambda-releases ; cd tmp; zip -r ../lambda-releases/results_joiner.zip *

	# clean up
	rm -rf tmp/

bootstrap:	
	cdk bootstrap --profile fed-a11y


deploy:
	cdk deploy --profile fed-a11y


destroy:
	cdk destroy --profile fed-a11y
