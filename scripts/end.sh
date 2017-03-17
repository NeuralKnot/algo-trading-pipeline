killall -9 python3 || echo "Done!"
killall -9 chromedriver || echo "Done!"
killall -9 Xvfb || echo "Done!"
while kill -0 $(pgrep python3) 2> /dev/null; do sleep 1; done;
while kill -0 $(pgrep chromedriver) 2> /dev/null; do sleep 1; done;
while kill -0 $(pgrep Xvfb) 2> /dev/null; do sleep 1; done;
