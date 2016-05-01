from setuptools import setup

setup(
    name='dmoj',
    version='0.1',
    packages=['dmoj'],
    entry_points={
        'console_scripts': [
            'dmoj = dmoj.judge:main',
        ]
    },
    install_requires=['watchdog', 'pyyaml', 'ansi2html', 'pika', 'termcolor'],

    author='quantum5',
    author_email='quantum2048@gmail.com',
    url='https://github.com/DMOJ/judge',
    description='The judge component of the Don Mills Online Judge platform',
    keywords='online-judge',
    classifiers=[
        'Development Status :: 3 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Education',
        'Topic :: Software Development',
    ],
)
