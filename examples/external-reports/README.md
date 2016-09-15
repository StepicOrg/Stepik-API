# Requirements

* Python 3: pypandoc, shutil, argparse
* PdfLaTeX

It is recommended to install TeX Live for compilation latex project to pdf.

      sudo apt-get install texlive-full

If you need to edit latex projects, you can install [TeXmaker](http://www.xm1math.net/texmaker/download.html).

# API keys
Get your keys at https://stepik.org/oauth2/applications/
(client type = confidential, authorization grant type = client credentials)

# Usage 

## Item Report
To build the item report for course with course_id, you should launch in the command line.

    python item_report.py --course course_id

or

    python item_report.py -c course_id
    
Report will be put in ``./pdf/course-{course_id}-item-report.pdf``

**Note:** Since course submissions can be extremely large, it it recommended to put the file ``course-{course_id}-submissions.csv`` in the folder ``./cache/``


## Video Report
To build the video report for course with course_id, you should launch in the command line.

    python video_report.py --course course_id

or

    python video_report.py -c course_id
    
Report will be put in ``./pdf/course-{course_id}-video-report.pdf``
