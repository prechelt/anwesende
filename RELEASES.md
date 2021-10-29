# a.nwesen.de Releases

Release dates, version numbers, and contents:


## Versions 0.x

- 2020-10-06, Version **0.1**: 
  - Started development: Use case descriptions
- 2020-10-21, Version 0.6: 
  - Basic functionality is complete:
    Login, reading Excel files, generating QR codes, visitor registration form,
    retrieving visit groups and writing Excel file
- 2020-10-28, Versison 0.7: 
  - User-visible process documentation
  - Demo mode
  - Automatic purging of visit data after retention time
- 2020-11-06, Version 0.8: 
  - Pilot deployment, deployment description
  - Load testing (about 1000 visits/minute: fast enough)
  - Logging


## Version 1.0

- 2020-12-29, Version **1.0**: 
  - `anw.sh` install script for mostly automated deployment


## Versions 2.x

- 2021-01-02, Version **2.0**:
  - introduced 2-dimensional seat numbering and distance calculation
  - This is a semi-incompatible change: Existing pasted QR codes
    will show e.g. seat 14, but will in fact now refer to seat r1s14;
    existing importstep objects will lose their seats.
- 2021-01-05, Version 2.1:
  - added FAQ page
  - updated `/import` (which had outdated documentation in version 2.0)
  - more info on the QR code snippets: URL, instruction
  - published at GitHub
- 2021-01-06, Version 2.2:
  - README now also describes DB restore and deployment identification
- 2021-03-14, Version 2.3:
  - now shows number of people in room after one has registered
  - introduced `DEPLOYMODE=DEVELOPMENT` for development
    and removed some outdated deployment-related stuff 
  - fixed mistakes in `anw.sh` script, install instructions, FAQ.
  - updated Python to 3.9 and removed Pillow dependency 
- 2021-03-29, Version 2.4:
  - fixed and improved import statistics display
  - added a usage statistics (data status) table page:  
    Organization, Department, #rooms, #seats, #visits
  - fixed a timezone issue
  

## Versions 3.x

- 2021-04-23, Version **3.0**:
  - introduced setting COOKIE_WITH_RANDOMSTRING for optionally turning off
    the unique cookie identifier that is normally included in the data
  - introduced setting USE_EMAIL_FIELD for optionally excluding the
    email address from the registration form (because some states do
    not mention this in their Infektionsschutzverordnung).
    Note that not having email adresses _greatly_ reduces the value of
    running a.nwesen.de in the first place. Not recommended!
  - created space for smartphone keyboard below the registration form
    to accomodate some ill-behaving browsers
  - Page `/qrcodes/x` now formats vertically on smartphones.
- 2021-05-21, Version 3.1:
  - now properly converted times from UTC to localtime in the Excel output.
- 2021-06-06, Version 3.2:
  - added show_rooms
  - introduced `GUNICORN_WORKERS` and `GUNICORN_THREADS` settings.
    These settings increase performance, in particular for servers with
    multiple CPUs.
    Existing installations must add this in their `.envs/myenv.env` file; 
    see `config/envs/myenv-template.env` for how this will look like.
  - The search dialog now ignores case (valuable for email!).  
  - fixed failure when retrieving contact groups for empty search results
- 2021-06-15, Version 3.3:
  - made access control stricter 
    (the usage statistics and show-QR-codes pages now require a login
    in order to reduce the confusion when a Datenverwalter's session expires,
    which would previously result in crippled output)


## Versions 4.x

- 2021-07-12, Version 4.0:
  - added columns `row_dist` and `seat_dist` for the distance (in meters)
    between rows (front-to-back direction) and seats (left-to-right direction), 
    respectively, so that different rooms can have seating arrangements
    of different density and still the distances computed are reasonably
    accurate.
    For existing rooms, 1.4m is assumed for both values.  
    The new columns can be added to the database by reading an updated version
    of previous Excel files with identical values of
    `organization`, `department`, `building`, and `room`.
    See FAQ 3.3 for a discussion.    
- 2021-08-17, Version 4.1:
  - corrected wrong columname in some file import "Excel error" messages
  - improved logging
  - `/show_rooms` now displays `row_dist` and `seat_dist`
  - made Excel import robust against non-text cell contents
- 2021-09-20, Version 4.2:
  - Limit of 99 seats and rows replaced by 2000 seats total.
  - faq.html now discusses U-shaped seating arrangements (a common hurdle
    for the understanding of room admins).


## Versions 5.x

- 2021-09-25, Version 5.0:
  - introduce `status_3g` vaccination status field and 
    `USE_STATUS_3G_FIELD` feature toggle to use it (default: `True`)
  - added FAQ 3.4 "Wie informiere ich meine Besucher_innen?" including
    a proposed hang-on-the-wall information.
- 2021-09-28, Version 5.1:
  - greatly improved `loadtest.py`
  - server setup hardened: Gunicorn: add `--max-requests 4000`;
    the generated `docker-compose.yml` will now specify `restart: unless-stopped`
  - when not logged in, properly redirect upon `/import` upload (instead of just failing)  
- 2021-10-29, Version 5.2:
  - visit form retrieves vaccinated&recovered states from cookie, 
    but tested state not
  - show visit form errors very prominently
  - search "Besuche finden" shows date and time
  - updated django Docker base image to python:3.9-slim-bullseye
  - catch exception for invalid cookies
  - made docker build process a lot leaner and faster
  - 

## Future

- already done for the next version:
  - ...


- TODO:
  - ...
