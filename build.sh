mkdir dist
pip install -r requirements.txt -t ./dist
cp service.py dist/service.py
cp roadmapper.py dist/roadmapper.py
cd dist
zip -r ../deploy.zip *
cd ..