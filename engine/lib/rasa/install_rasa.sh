WD=$(pwd)

echo "installing in $WD"

# Update the Raspberry Pi
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get dist-upgrade -y

# Install initial build dependencies
# Provides
# Enables pip3.6 to access pypi
sudo apt-get install libbz2-dev libssl-dev -y

# Get and install Python3.6
wget https://www.python.org/ftp/python/3.6.8/Python-3.6.8.tar.xz
tar -xvf Python-3.6.8.tar.xz
cd Python-3.6.8
sudo ./configure
sudo make -j4
sudo make install

# Update Python3.6 packages
python3.6 -m pip install --upgrade pip setuptools --user

# Install additional dependencies
# Enables access to Tensorflow whl
# Dependency for the h5py python package
sudo apt-get install python3-pip libhdf5-dev -y

# Install Tensorflow
python3.6 -m pip install tensorflow==1.14.0 --user

# Install OpenCV Dependencies
sudo apt-get install build-essential cmake unzip pkg-config -y
sudo apt-get install libjpeg-dev libpng-dev libtiff-dev -y
sudo apt-get install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev -y
sudo apt-get install libxvidcore-dev libx264-dev -y
sudo apt-get install libgtk-3-dev -y
sudo apt-get install libcanberra-gtk* -y
sudo apt-get install libatlas-base-dev gfortran -y
sudo apt-get install python3-dev -y

# Download OpenCV and clarify naming scheme
cd $WD
wget -O opencv.zip https://github.com/opencv/opencv/archive/4.0.0.zip
wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/4.0.0.zip
unzip opencv.zip
unzip opencv_contrib.zip
mv opencv-4.0.0 opencv
mv opencv_contrib-4.0.0 opencv_contrib

cd $WD/opencv
mkdir build
cd build

cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_INSTALL_PREFIX=/usr/local \
    -D OPENCV_EXTRA_MODULES_PATH=$WD/opencv_contrib/modules \
    -D ENABLE_NEON=ON \
    -D ENABLE_VFPV3=ON \
    -D BUILD_TESTS=OFF \
    -D OPENCV_ENABLE_NONFREE=ON \
    -D INSTALL_PYTHON_EXAMPLES=OFF \
    -D BUILD_EXAMPLES=OFF ..

# Increasing swap size to make OpenCV
SWAPSIZE=2048
sed -i "s/^CONF_SWAPSIZE.*/CONF_SWAPSIZE=${SWAPSIZE}/" /etc/dphys-swapfile

# Restarting swap service
sudo /etc/init.d/dphys-swapfile stop
sudo /etc/init.d/dphys-swapfile start

# Make OpenCV
make -j4

# Install OpenCV
sudo make install
sudo ldconfig

# Reseting swap size
SWAPSIZE=100
sed -i "s/^CONF_SWAPSIZE.*/CONF_SWAPSIZE=${SWAPSIZE}/" /etc/dphys-swapfile

# Restarting swap service
sudo /etc/init.d/dphys-swapfile stop
sudo /etc/init.d/dphys-swapfile start

# Link cv2 to Python3.6
cd /usr/local/lib/python3.6/site-packages/
sudo ln -s /usr/local/python/cv2/python-3.6/cv2.cpython-36m-arm-linux-gnueabihf.so cv2.so

# In case git is not installed
sudo apt-get install git -y

# Getting codebases for spaCy, tensor2tensor, and RASA
# NOTE: This is hard-coded for rasa-1.4.0 right now - let's make it more elegant soon
cd $WD
git clone https://github.com/explosion/spaCy
git clone https://github.com/tensorflow/tensor2tensor
git clone https://github.com/google/dopamine.git
wget https://github.com/RasaHQ/rasa/archive/1.4.0.zip && unzip 1.4.0.zip

# Installing spaCy
export BLIS_ARCH=generic
cd $WD/spaCy
python3.6 -m pip install -r requirements.txt --user
python3.6 setup.py build_ext --inplace
python3.6 -m pip install . --user

# Installing dopamine-rl
cd $WD/dopamine
sed -i '/opencv-python/d' setup.py
python3.6 -m pip install . --user

# Installing tensor2tensor
cd $WD/tensor2tensor
sed -i '/opencv-python/d' setup.py
sed -i '/dopamine-rl/d' setup.py
python3.6 -m pip install . --user --force-reinstall

# Installing other RASA dependencies
sudo apt install libpq-dev/buster -y
python3.6 -m pip install psycopg2 --user

# Installing RASA
cd $WD/rasa-1.4.0
sed -i '/tensor2tensor/d' setup.py
sed -i '/tensor2tensor/d' requirements.txt
python3.6 -m pip install -r requirements.txt --user --force-reinstall
python3.6 -m pip install . --user --force-reinstall

# Script exit
echo ""
echo ""
echo "------------------------------------------------------------"
echo "Congratulations! Rasa is now installed on your Raspberry Pi."
echo "To test rasa out, run python3.6 -m rasa init and start "
echo "creating your bot!"