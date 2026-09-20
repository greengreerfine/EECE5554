from setuptools import find_packages, setup

package_name = 'eece5554_pa1'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jojo',
    maintainer_email='zhang.zhiqi2@northeastern.edu',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
	    'talker = eece5554_pa1.talker:main',
            'listener = eece5554_pa1.listener:main',
	
        ],
    },
)
