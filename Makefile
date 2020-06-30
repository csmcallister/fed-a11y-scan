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


build_site_mapper:
	
	# make a python dir for layer
	mkdir -p python/lib/python3.8/site-packages
	
	cp lambdas/site_mapper/requirements.txt ./reqs.txt
	# run dep installation in AWS Linux docker image and write to local dir
	docker run -v ${PWD}:/var/task "lambci/lambda:build-python3.8" /bin/sh -c "pip install -r ./reqs.txt -t python/lib/python3.8/site-packages/; exit" && \
	zip -r lambda-releases/site_mapper_layer.zip python > /dev/null
	
	rm -rf python/
	rm reqs.txt


bootstrap:	
	cdk bootstrap --profile fed-a11y-scan


deploy:
	cdk deploy --profile fed-a11y-scan


destroy:
	cdk destroy --profile fed-a11y-scan
