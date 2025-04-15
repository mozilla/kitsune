from kitsune.questions.llm import is_spam, select_topic


TOPIC_CLASSIFIER_EVAL_SUITE_1 = [
    {
        "question": (
            "Background: I have Firefox on a brand new Thinkpad X1 Gen 11, "
            "running Windows 11. I have used Firefox with multiple Google "
            "accounts on an older machine for 5+ years. That machine is "
            "running Windows 11 as well. \r\n"
            "\r\n"
            "Problem: I cannot add multiple Google accounts in order to "
            "access Gmail, Drive, etc. I have added the first, my personal "
            'account. When I select "Add another account" from the menu icon '
            "in Gmail website, it takes me to the add account page. As soon "
            "as I try to highlight the name of my personal account, it "
            "freezes and the only option is to shut it down. To be clear, "
            "this is trying to add a Google account when browsing, *not* "
            "trying to create multiple profiles in Firefox. I have "
            "refreshed, reinstalled, and searched for a solution. What is "
            "going on?"
        ),
        "topic": "Performance and connectivity > Crashing and slow performance > App "
        "responsiveness",
    },
    {
        "question": "<i>duplicate of [/questions/1477877] thread</i>\r\nrestore my vpn",
        "topic": "Undefined",
    },
    {
        "question": "When Firefox opens it opens 2 additional tabs. I have not "
        "changed anything in settins. Syarted happening a few weeks ago. "
        "How can i prevent Firefox from opening2 extra tabs?",
        "topic": "Browse > Tabs",
    },
    {
        "question": "fire fox keeps blocking my bank account web site",
        "topic": "Performance and connectivity > Site breakages"
        " > Blocked application/service/website",
    },
    {
        "question": "i want my link page to be hook www.patnsamdailypay.com",
        "topic": "Browse > Home screen",
    },
    {
        "question": "Hello Team, I am trying to install extensions to my Firefox on "
        "Macbook Pro M3.\r\n"
        "\r\n"
        "Getting error in the subject\r\n"
        "\r\n"
        "An unexpected error occurred during installation.\r\n"
        "\r\n"
        "Extensions I have tried to install so far:\r\n"
        "AdBlock for Firefox by AdBlock\r\n"
        "uBlock Origin by Raymond Hill\r\n"
        "\r\n"
        "Both are failing with the same error.\r\n"
        "\r\n"
        "I have tried reinstalling Firefox, Private Window, nothing "
        "helped. It did work for me with Firefox on Macbook Intel",
        "topic": "Settings > Add-ons, extensions, and themes > Extensions",
    },
    {
        "question": "i desperately need to recover my prior bookmarks, i lost them "
        "when i reset my computer, plse help",
        "topic": "Backup, recovery, and sync > Recover data",
    },
    {
        "question": "'''I cannot sign to firefox'''   HELP, HELP, HELP,HELP        " "Thank you.",
        "topic": "Passwords and sign in > Sign in",
    },
    {
        "question": "Unable to view YouTube comments using Firefox on android. I can "
        "view the comments on Opera, duckgo and chrome. \r\n"
        "\r\n"
        "This problem started about four days ago. Comments show on the "
        "short videos but not the regular videos. When I tap on "
        '"comments" the resulting page/frame is empty.',
        "topic": "Performance and connectivity > Site breakages",
    },
    {"question": "Solved", "topic": "Undefined"},
    {
        "question": "When trying to open sites from my email, such as usps.com, I "
        "get the following message and it will not allow me to open it "
        "even if I put the address in myself:\r\n"
        "\r\n"
        "Hmm. We’re having trouble finding that site.\r\n"
        "\r\n"
        "We can’t connect to the server at tools.usps.com.\r\n"
        "\r\n"
        "If you entered the right address, you can:\r\n"
        "\r\n"
        "    Try again later\r\n"
        "    Check your network connection\r\n"
        "    Check that Firefox has permission to access the web (you "
        "might be connected but behind a firewall)\r\n"
        "\r\n"
        "PLEASE help me find this problem. Until the last update, I "
        "didn't have this problem. What do I need to do?\r\n"
        "Thank you",
        "topic": "Performance and connectivity > Site breakages",
    },
    {
        "question": "I don't know where to add shortcuts all at once instead of "
        'adding each one individually, I tried to search for a "shortcut '
        'folder" within the bookmarks manager and i found nothing, is '
        "there anything I can do to move opera browser's speed dial "
        "bookmarks into firefox shortcut",
        "topic": "Settings > Import and export settings",
    },
    {
        "question": "I restarted my desktop using Microsoft OS and can't get Firefox "
        "to browse like Edge does.\r\n"
        "Any thoughts?",
        "topic": "Performance and connectivity",
    },
    {
        "question": "How do I get rid of the new sidebar permanently. Also why as a "
        "company do you guys feel the need to shoot yourself in the foot "
        "so aggressively and so repeatedly.",
        "topic": "Settings > Customization > Browser appearance",
    },
    {
        "question": "I can not loging-  what is the problem",
        "topic": "Passwords and sign in",
    },
    {
        "question": "I signed in to be sure to save my bookmarks and i lost them "
        "instead. When i hit sync, i wanted to backup my current "
        "bookmarks. Instead, I lost them. It reverted to the old "
        "bookmarks i had a few weeks ago. I lost all of my bookmarks "
        "from the last few weeks. HELP!",
        "topic": "Backup, recovery, and sync > Recover data",
    },
    {
        "question": "I can't find the menu bar anywhere and trying to locate my "
        "bookmarks. Just downloaded firefox to my new computer and it's "
        "not syncing",
        "topic": "Backup, recovery, and sync > Sync data > Sync failure",
    },
    {
        "question": "After the update to 128.5.1esr the browser restarted and it had "
        "the default search providers again. Why??? I was not prompted "
        "to approve it, there was no notification either. This is the "
        "st*pid sh*t which pushes users away from Firefox. \r\n"
        "\r\n"
        "I absolutely hate Bing in the first place.",
        "topic": "Settings",
    },
    {
        "question": "I need help transferring my bookmarks to a new Mac computer\r\n"
        "I created a Mozilla account, that was verified, but on the new "
        'computer I cant find anywhere to enable "sync now"\r\n'
        "Can you help me transfer these bookmarks?",
        "topic": "Backup, recovery, and sync > Sync data > Sync configuration",
    },
    {
        "question": "This is the error message I get when I try to connect to "
        "different sites:\r\n"
        "\r\n"
        "Secure Connection Failed\r\n"
        "\r\n"
        "An error occurred during a connection to accounts.firefox.com. "
        "PR_END_OF_FILE_ERROR\r\n"
        "\r\n"
        "Error code: PR_END_OF_FILE_ERROR\r\n"
        "\r\n"
        "    The page you are trying to view cannot be shown because the "
        "authenticity of the received data could not be verified.\r\n"
        "    Please contact the website owners to inform them of this "
        "problem.\r\n"
        "\r\n"
        "Learn more…",
        "topic": "Performance and connectivity > Error codes > Web certificates",
    },
    {
        "question": "update turns off and on the monitor, it restarts randomly.",
        "topic": "Performance and connectivity > Crashing and slow performance",
    },
    {
        "question": "I understand how to work with my list of passwords in Firefox. "
        "And I understand that a user name seems to be associated with "
        "the specific website that it was used on. Recently I brought up "
        "intuit.com and expected there to be only 1 username,  but I saw "
        "a user name ''(Yahoo email address)'' that belongs to a guy "
        "that does some work for me. I remember him using my laptop to "
        "login to yahoo once to get something from his email. But he "
        "didn't use intuit.com. Not sure he even knows what intuit would "
        "be.\r\n"
        "\r\n"
        "So I went to the password list in firefox and typed in intuit, "
        "his user name didn't appear. I tried typing in his email "
        "address but it didn't find it. I'm not worried about any "
        "security issues. But I want the name removed from the list of "
        "users that pops up.\r\n"
        "\r\n"
        "I deleted the cookies for intuit but the user names still pop "
        "up.\r\n"
        "\r\n"
        "Any suggestions on how to get rid of this user name?",
        "topic": "Passwords and sign in > Save passwords",
    },
    {
        "question": "I don't like the new Firefox Browser Platform. I'm Old and "
        "Cranky. I can't find all my buttons. Help!? Is the old format "
        "gone forever?\r\n"
        "Martha S.",
        "topic": "Settings > Customization > Browser appearance",
    },
    {
        "question": "The browser keeps crashing. I want to remove it from my Win 10 "
        "computer but uninstall only lets me do a refresh. I need to "
        "remove it to see if it is Firefox or some other issue. How do I "
        "remove the software?\r\n"
        "\r\n"
        "Thanks for your help with this matter.\r\n"
        "\r\n"
        "Best regards,\r\n"
        "\r\n"
        "Adrian",
        "topic": "Performance and connectivity > Crashing and slow performance > App " "crash",
    },
    {
        "question": "Hello, \r\n"
        "\r\n"
        "I am new to Firefox and accidentally opened an account with the "
        "wrong email address. A code was sent to an active email address "
        "that I don't own. I created a second account which is the one "
        "that i'm asking this question from. \r\n"
        "\r\n"
        "My question is how I secure this account from being used by the "
        "other email account I accidentally had my code sent to? \r\n"
        "\r\n"
        "Thank you for help.",
        "topic": "Accounts",
    },
    {
        "question": "Started 2 weeks ago where I am getting ad blocker pop ups on a "
        "lot of web sites I have used in the passed with no errors.\r\n"
        "now getting the blocker everyday.",
        "topic": "Settings > Add-ons, extensions, and themes > Extensions",
    },
    {
        "question": "For quite some time (months), the Alarm.com web page has not "
        'worked properly.  I get the message "Oops...Something went '
        "wrong.\r\n"
        "\r\n"
        "Don't worry your system is fine; it's just an internet "
        'thing."\r\n'
        "\r\n"
        "Refresh does NOT solve the problem.   Today I resorted to using "
        "Edge, and all worked well.  It's clearly a Firefox problem.   "
        "Can you tell me what's going on?  Is there a fix?  I'm "
        "disappointed that Firefox can't deal with a web page.",
        "topic": "Performance and connectivity > Site breakages > Web compatibility",
    },
    {
        "question": "Recently I have been unable to sign in on several different "
        "sites, but have had no problem on others.  This is a new "
        "computer with Windows 11, and I set it up about a week ago.  "
        "When I tried to purchase a You Tube TV subscription, the "
        "purchase locked up.  I tired it with Chrome and no problem.  "
        "When I tried to log into my credit card account with Chase, I "
        "got an error message suggesting I try later or use another "
        "browser.  Again Chrome worked.  Then I tried to log into Aflac "
        "and got a message saying the site wasn't redirecting properly.  "
        "Again Chrome worked.  Also Firefox worked for Aflac on an older "
        "computer.\r\n"
        "\r\n"
        "I don't want to use Chrome.  Can anyone help?\r\n"
        "Andy",
        "topic": "Performance and connectivity > Site breakages",
    },
    {
        "question": "Hello beautiful angel 😇 how are you doing today 🥰❤️",
        "topic": "Undefined",
    },
    {
        "question": "I am unable to connect with several secure sites.  Why? \r\n"
        "\r\n"
        " Nancy G. [edited email from public support forum]",
        "topic": "Performance and connectivity",
    },
    {
        "question": "need to import bookmarks from my older comp. to this new comp.",
        "topic": "Backup, recovery, and sync > Recover data",
    },
    {
        "question": "Is this something to be concerned about with future sites, or "
        "is this an unfortunate, isolated incident? One of my local "
        "utility companies is not going to be supporting the use of "
        "Firefox on their website any longer. Has anyone else seen "
        "anything like this on other sites, or has this been brought up "
        "elsewhere? Frankly I find it outrageous and is forcing me and "
        "others to use Chromium based browsers (aside from Safari which "
        "I don't use).\r\n"
        "\r\n"
        "* I emailed the company asking for an explanation, and I'm "
        "awaiting a reply. \r\n"
        " \r\n"
        "I would share the URL for others to email and help press the "
        "company on the issue, but wasn't sure of the guidelines of the "
        "forum or if that was appropriate. I'm just irritated and "
        "venting sorry =/",
        "topic": "Privacy and security > Tracking protection > Cookies",
    },
    {"question": "connectivity problem", "topic": "Performance and connectivity"},
    {
        "question": "With the last couple of updates to Firefox (now running v133) "
        "on Windows 10 I noticed that there is a new search bar that "
        "overwrites the tabs on top of the Firefox window when I click "
        "into the URL bar, which is set up to be used for search.  This "
        "began to happen recently but I'd like to know how to configure "
        "Firefox to do search like it used to, in the URL bar not a new "
        "search bar, and disable this new search bar that disorients me "
        "when it pops up and disappears.",
        "topic": "Settings > Customization > Browser appearance",
    },
    {"question": "How to find Spam /Junk?", "topic": "Undefined"},
    {
        "question": '"Entry point not found"\r\n' "Can I get help to get firefox going again?",
        "topic": "Performance and connectivity > Error codes",
    },
    {
        "question": "The site has a yellow color with Firefox, I don't know the "
        "reason, please help me",
        "topic": "Performance and connectivity > Site breakages",
    },
    {
        "question": "I connot seem to removea auto fill username from a sensitive "
        "page. ive tried in thsetting in privacy and security",
        "topic": "Settings > Autofill",
    },
    {
        "question": "Cant remove a username from a sensative site have tried in "
        "settings privacy and security but ikeeps auto filling",
        "topic": "Settings > Autofill",
    },
    {
        "question": "So i reinstalled my graphics driver yesterday, and after that "
        "when i open a pdf on firefox it only shows blackscreen. it "
        "didnt happen on other browsers(chrome, edge)",
        "topic": "Browse > Images and documents > PDFs",
    },
    {
        "question": "Try to log into my Subway account get message after time out at "
        'first attempt "Secure connection Failed"\r\n'
        "\r\n"
        "How do I get around this?\r\n"
        "\r\n"
        "Bye\r\n"
        "\r\n"
        "Dean Dickson\r\n"
        "deand@internode.on.net",
        "topic": "Performance and connectivity > Error codes > Web certificates",
    },
    {
        "question": "hdfc bank net banking page not opening",
        "topic": "Performance and connectivity > Site breakages",
    },
    {
        "question": "not getting any energy for past two weeks. Will soon run out of "
        "the energy I have.",
        "topic": "Undefined",
    },
    {
        "question": "Whenever i try to access a well reputed website i got this "
        "error 'SEC_ERROR_UNKNOWN_ISSUER'.",
        "topic": "Performance and connectivity > Error codes",
    },
    {
        "question": "I upgraded from Ubuntu 18.04 to 22.04. I cannot find my deleted "
        "mail. The trash box is empty. Not sure its working. Can you "
        "help please?",
        "topic": "Undefined",
    },
    {
        "question": "Dear Sir/Madam,\r\n"
        "\r\n"
        "I have recently found some sites that do not open in Firefox, "
        "however, in Chrome everyhing is fine. This was one of them: "
        "https://sciendo.com/article/10.2478/jdis-2025-0002\r\n"
        "\r\n"
        "The other one was a login page for an Admin site - that is not "
        "suitable for testing, since it contains confidential data.\r\n"
        "\r\n"
        "Could you please check it?\r\n"
        "\r\n"
        "Thanks, Krisztina Kőrösi",
        "topic": "Performance and connectivity > Site breakages > Web compatibility",
    },
    {"question": "http://172.17.0.19/vdd/", "topic": "Undefined"},
    {
        "question": "Hi\r\n"
        "FF : the proposed update ,133.0, cannot be made\r\n"
        "From 131.0.2 to 133.0.\r\n"
        "MacOS 10.15.7\r\n"
        "Is a new release or a patch planned?\r\n"
        "\r\n"
        "Best regards\r\n"
        "Peny",
        "topic": "Installation and updates > Update",
    },
    {
        "question": "Hi, I have problem for import my bookmark.\r\n"
        "I installed firfox from snapstore. i uninstall it and then "
        "again installed it from snapp store.\r\n"
        "after re-installing i want to signin in my account and then "
        "import my bookmarks & passwords.\r\n"
        "so i enter my email(i always use this email) but for the "
        "password i forgoted it so i click on change password and change "
        "it so i entered to my account with new password  now here my "
        "problems started :   i cant import data ! there is nothing! "
        "why? :( in another try i  cick on import browser data it shows "
        "me this options import bookmarks from html or csv file.\r\n"
        "but i dont have these files!\r\n"
        "so my question is  how can i import my previouse booksmarks and "
        "password ?!  i really need them :(\r\n"
        "\r\n"
        "thankyou for your help!\r\n"
        "\r\n"
        "Ubuntu 24.04.1 LTS - my firfox version : 133.0 (64-bit)",
        "topic": "Settings > Import and export settings",
    },
    {
        "question": "When I search on the NTP or Homepage, the sidebar/tab-bar "
        "expands on my left with the different websites search previews. "
        "When I use my mouse to click on one of the suggested sites it "
        "does not take me to the website, it goes blank. But when I use "
        "the keyboard arrows to choose a site then press enter, only "
        "then it opens the website.\r\n"
        "\r\n"
        "Hope I made it clear enough?\r\n"
        "\r\n"
        "Thanks,",
        "topic": "Settings > Customization > Browser appearance",
    },
    {
        "question": "I have a Raspberrypi 400. My mouse cursor became the Firefox "
        "icon. How do I get it back to normal permanently?",
        "topic": "Settings > Customization > Browser appearance",
    },
    {
        "question": "I received an email from my wife with a picture on it and I "
        "wanted to pass it on to Facebook , there was no share  on it "
        "when I right clicked my mouse ,like I ave done in the passed "
        ".Can you help me to be able to pass on the picture Thank You "
        "Pete",
        "topic": "Browse",
    },
    {
        "question": "Firefox on MacOS in full screen mode makes the black offset "
        "between the screen edge and the Firefox window after logging in "
        "after MacOS is locked.\r\n"
        "It fixes itself when you exit the full screen and enter it "
        "again.\r\n"
        "\r\n"
        "How to reproduce?\r\n"
        "* Open Firefox and enter the full screen mode\r\n"
        "* Close your MacBook and wait until it prompts you for your "
        "password or touch id\r\n"
        "* The Firefox window has black offset between screen edge and "
        "the Firefox window, that was not present before\r\n"
        "* Exit the full screen and get into it again, and the offset is "
        "gone",
        "topic": "Performance and connectivity",
    },
    {
        "question": "Hello, Mozilla Fire Support, thank you for your round-the-clock "
        "efforts. Please add Persian to the translation of the site, "
        "considering that Iran ranks third in Mozilla usage out of a "
        "country of 100 million.  İ hope Your kindness is growing day by "
        "day.\r\n"
        " Mahbod",
        "topic": "Settings > Languages",
    },
    {
        "question": "I lost all my Bookmark post system reinstall, please help me to "
        "recover my bookmark from my firefox account",
        "topic": "Backup, recovery, and sync > Recover data",
    },
    {
        "question": "hello\r\n"
        "last few days this started.... been in dark mode for years "
        "now,,,, on utube trying to add a comment,,, the typing is "
        "blacked out so i cant see it until after its posted .. i can "
        "search on utube as the text comes out white ,, just while "
        "making a comment it is black on black and cant see what i am "
        "typing ,,, the comment when posted shows up as white on black "
        "..\r\n"
        "hope thats easy to fix lol\r\n"
        "thanks mike",
        "topic": "Performance and connectivity > Site breakages",
    },
    {
        "question": "Dear Sirs,\r\n"
        "\r\n"
        "For at least the last two weeks, I have experienced a lot of "
        "trouble working with Mozilla Firefox.  Just reading my emails "
        "is an arduous task.\r\n"
        "\r\n"
        'It crashes, I lose internet connection, it does not "respond," '
        "etc., and Symantec Norton 360 cannot find out WHY!  I have "
        "deleted Firefox and reinstalled it, and it is still "
        "unreliable.\r\n"
        "\r\n"
        "Before I have to resort to using another browser, can YOU tell "
        "me what is going on.  I have a Dell desktop, using Windows 10 "
        "Pro (obtained in 2018). Firefox is my default browser. I also "
        "have Google Chrome installed.\r\n"
        "\r\n"
        "Please help!\r\n"
        "\r\n"
        "Sincerely yours,\r\n"
        "\r\n"
        "Victoria-Ann Bonanni\r\n"
        "[email address]",
        "topic": "Performance and connectivity > Crashing and slow performance > App "
        "responsiveness",
    },
    {
        "question": "I have looked on the web and continue to find all sorts of "
        "references on how to configure your browser to open the tabs I "
        'had open last time I closed the browser.  I have the "Open '
        'previous windows and tabs" checked in the General '
        "settings....and it doesn't work!  How is that?  Any special "
        "thing I need to do to get it to work?",
        "topic": "Settings",
    },
    {
        "question": "After Firefox update have no recent Bookmarks",
        "topic": "Backup, recovery, and sync > Recover data",
    },
    {
        "question": "Why do I have to re-register with my banking website to "
        "remember my settings in order to not need two-factor "
        "authentication?  I have selected in Preferences/settings for "
        "that website's cookies, etc, to be retained in Firefox.",
        "topic": "Privacy and security > Tracking protection > Cookies",
    },
    {"question": "'''bold text'''", "topic": "Undefined"},
    {
        "question": "Why has Firefox recently started closing all open tabs between "
        "browsing sessions when the system has not been re-started or "
        "updated to my knowledge?  This is a major compromise of "
        "utility.",
        "topic": "Settings",
    },
    {
        "question": "I'm putting off upgrading Linux as I have many hundreds of "
        "undocumented addons which will be lost and would take forever "
        "to attempt to remember how to re-install.\r\n"
        "\r\n"
        "(in fact I might just switch to macos and try using "
        "homebrew).\r\n"
        "\r\n"
        "It seems very harsh that upgrading Firefox has been prevented "
        "by linux mint for years now.\r\n"
        "\r\n"
        "Yes Homebrew is perhaps the way forward! Life would be easier "
        "with just one O/S as I need Macos anyway for adobe lightroom.",
        "topic": "Installation and updates > Update",
    },
    {
        "question": "How do I make the scroll bar always visible? The fact that you "
        "have to hover over it before it shows itself is maddening! "
        "Makes scrolling so much more difficult and frustrating. If this "
        "can't be adjusted I am done with mozilla after many many years "
        "of using it.",
        "topic": "Settings > Customization > Browser appearance",
    },
    {
        "question": "I need help to connect to the fireFox",
        "topic": "Performance and connectivity > Site breakages",
    },
    {
        "question": "Presently my firefox installation is on my C: drive (disk 0), "
        "however it tends to be overworked so I want to move my D: drive "
        "(disk 1) is there a simply way to this without having to "
        "uninstall and then reinstall firefox?",
        "topic": "Installation and updates",
    },
    {
        "question": "after an updated of fire fox on windows 10 have lost access to "
        "fire fox how do i restore it? \r\n"
        "i want  to get my password and my book marks?",
        "topic": "Backup, recovery, and sync > Recover data",
    },
    {
        "question": "My version of Firefox is 108.0.1 -- I am running Windows 10 on "
        "a machine that Windows says is not capable of running Windows "
        "11\r\n"
        "\r\n"
        "My installation of Firefox resides on my D: drive.  It uses "
        "quite a bit of space for cache and other things on my C: drive "
        "but it starts and runs on my D: drive.Now I am forced to "
        "update, but I can't get the installer to recognize an "
        "installation on the D: drive and update it.  Instead it makes a "
        "new installation on my C: drive and I lose my appearance "
        "customizations, history and bookmarks.\r\n"
        "\r\n"
        "I have never believed and cannot accept that an application "
        "absolutely MUST reside on the C: drive.  It's lazy programming "
        "(something I used to do for a living).  I can't believe Mozilla "
        "programmers wrote an installer that insists that Firefox must "
        "live there, so what am I missing?  How do I tell the installer "
        "to find and update my existing application?\r\n"
        "\r\n"
        "Thanks for your help.  I feel as if I am missing something that "
        "ought to be obvious.",
        "topic": "Installation and updates > Update > Update failure",
    },
    {
        "question": "My organization uses Box Drive for file storage/transfer. I "
        "recently upgraded to an ARM-based PC (Microsoft Surface) which "
        "the Box app does not support, forcing me to use a browser to "
        "access my files.\r\n"
        "\r\n"
        "When I upload a file to Box via Firefox, it repeatedly uploads "
        "the same file until I close the browser. I only noticed this "
        "after coming back to the tab and noticing that the PDF I "
        "uploaded was on version 1,937 and counting. I tested another "
        "file and observed the same behavior.\r\n"
        "\r\n"
        "The behavior persists when using a private window with all "
        "extensions disabled.\r\n"
        "\r\n"
        "The bug does not appear to affect Chrome: files upload once as "
        "expected.\r\n"
        "\r\n"
        "In Firefox, other services such as Dropbox and Google Drive are "
        "not affected, only Box.\r\n"
        "\r\n"
        "Anybody else experienced this and found a solution?",
        "topic": "Performance and connectivity > Site breakages > Web compatibility",
    },
    {
        "question": "I was receiving duplicate diaglog in the GolfWRX forums such as "
        "member name showing twice. I cleared cookies and now the "
        "website only shows what looks like a table of content page, I "
        "see no details or graphics.",
        "topic": "Performance and connectivity > Site breakages",
    },
    {
        "question": "I am consistently getting a popup as follows from Norton: We "
        "prevented your connection to pushtorm.net because it is a "
        "dangerous webpage. Threat catagory:URL:Block (fake scan). "
        "details as follows: \r\n"
        "URL https://pushtorm.net/worker.js\r\n"
        "Process C:\\program files/Mozillafirefox/firefox.exe\r\n"
        "Detected by : Safeweb.\r\n"
        "I cannot seem to make it go away. Gives me no options. Just "
        "keeps popping up every several minutes and you have to X it to "
        "be able to do anything.. Solution?????",
        "topic": "Performance and connectivity > Error codes",
    },
    {
        "question": "Cannot opt out of continuous emails and messages from specific "
        "companies...Hilton, for example",
        "topic": "Undefined",
    },
    {"question": "Please request", "topic": "Undefined"},
    {
        "question": "It cant reload i need help",
        "topic": "Performance and connectivity > Crashing and slow performance > App "
        "responsiveness",
    },
    {"question": "I'm unable to get into my credit card account", "topic": "Undefined"},
    {
        "question": "How do I set my home page with my yahoo mail account?  I looked "
        "under your help section and followed instructions and it didn't "
        "work.  I am currently setting up my new computer.",
        "topic": "Browse > Home screen",
    },
    {
        "question": "until sunday me youtube page stops working.Can you help me " "please.",
        "topic": "Performance and connectivity > Site breakages",
    },
    {
        "question": "Somehow I cannot open images of something I went to see when I "
        "use the search engine. I can get videos and shopping, but not "
        "images.  Appreciate a solution.",
        "topic": "Browse > Images and documents > Images",
    },
    {
        "question": "About a month ago I found that, when I clicked on Firefox "
        "browser, instead of the usual page with the default search "
        "engine duckduckgo coming up, a very plain page which just said "
        '"Search"  appeared on screen with an address in the search bar '
        'which said something like "hp-search xxxxxxx".  And when I '
        "entered the address I required it was clear that Yahoo was "
        "doing the search.  \r\n"
        "I tried deleteing Mozilla from the Windows 10 control panel and "
        "then reinstalling it but each time I did this Firefox seemed to "
        "have been replaced by hp-searchxxxx  and Yahoo.\r\n"
        "Eventually, after using an alternative uninstaller (Revo), I "
        "was able to remove and replace Mozilla with the genuine browser "
        "and search engine.\r\n"
        'I have a feeling it was when I added "Privacy Badger" or some '
        "other extension to Mozilla that the trouble occurred. \r\n"
        "Has anyone else had this problem and, if so, could they please "
        "tell me what I error I made?",
        "topic": "Browse",
    },
    {
        "question": "Hi, the other day I upgraded from Windows 10 to Windows 11.  "
        "Long story short, I had to reinstall Windows 11 and all my "
        "apps, including Firefox.  My visited links no longer change "
        "color.  I tried the Settings / Language & Appearance / Manage "
        "Colors and nothing works.  I did notice that if I click on a "
        "link, it changes color for a fraction of a second then reverts "
        "back.  On a similar note, I use NoScript.  I've noticed it "
        "looks different.  Maybe a background grid.  And Privacy Badger "
        "is missing the oval slider boxes and the colored selection tab "
        "has no color.  I'm guessing this is all related somehow.",
        "topic": "Settings > Add-ons, extensions, and themes > Extensions",
    },
    {
        "question": "I can't send emails.",
        "topic": "Undefined",
    },
    {
        "question": "The HOME icon used to appear on Firefox on my old computer, now "
        "it does not appear on the URL line.  How do I get it to appear?",
        "topic": "Settings > Customization",
    },
    {"question": "Plce requst Auto otp in my dvice", "topic": "Accounts"},
    {
        "question": "I use Protonmail - a web-based email app.  They do not provide "
        "spellchecking, but say that the Firefox spellchecker should "
        "work in their email composer (it used to work so for me!) but, "
        "despite having Settings/General/Spellchecker ticked, and a "
        "dictionary (GB) selected (and, I see, the spellchecker working "
        "in this dialogue box) it is not working in the Protonmail "
        "composer.\r\n"
        "\r\n"
        "Help!!",
        "topic": "Undefined",
    },
    {
        "question": "How can I enable javascript to validate a pdf form?",
        "topic": "Settings",
    },
    {
        "question": "let me open specific websites i want to use",
        "topic": "Performance and connectivity",
    },
    {
        "question": "I accidentally activated 'block element' for my homepage "
        "'www.msn.com'.  Now the site comes up blank.  How do I reverse "
        "the 'block element?",
        "topic": "Performance and connectivity > Site breakages > Blocked "
        "application/service/website",
    },
    {
        "question": 'I first noticed this issue on "Zen Browser" which is based on '
        "firefox source code, but some time after i re-installed Firefox "
        "and noticed the issue was on Firefox, like, literally the same "
        "lag that happened on Zen was happening on Firefox.\r\n"
        "I tried deleting the .mozilla(.zen for Zen) and still nothing. "
        "i did noticed some things:\r\n"
        " - When i start Firefox on safe mode, the lag doesn't happen\r\n"
        " - On my brother user on the PC, the lag simply didn't "
        "happen\r\n"
        " - When the lag is happening, the disk reading goes REALLY "
        "high: \r\n"
        "I'll put a screenshot of the disk reading usage, even if it's "
        "on Zen executable, remember that the same issue is also "
        "happening on Firefox (and was where i noticed the disk usage "
        "thing)",
        "topic": "Performance and connectivity",
    },
    {
        "question": "Hi,  I ran a Firefox update which I guess I downloaded "
        "yesterday but now Firefox won't fully load new tabs with my "
        "usual view of stories. I don't know if that's the only part "
        "that's broken or what....I'm not geeky enough to say.  The "
        '"thought provoking stories" section just looks like its in a '
        "long process trying to connect with something.... all other "
        "windows I'd left pinned and recent activity shortcuts at the "
        "bottom of a new tab work.",
        "topic": "Performance and connectivity",
    },
    {
        "question": "Why do I see (16) Firefox accounts open in my Task Manager when "
        "my desktop Firefox browser doesn't show anything open?",
        "topic": "Performance and connectivity",
    },
    {"question": "how do i put a shortcut Firefox icon icon on my screen", "topic": "Undefined"},
    {
        "question": "I understand Firefox has always had a bit of an issue with SVG "
        "- and the 'Firefox has higher standards' doesn't really cut "
        "it.\r\n"
        "\r\n"
        "I personally love Firefox but the number of users doesn't "
        "warrant spending much time redevloping sites to overcome a "
        "shortcoming that no other browser has.\r\n"
        "\r\n"
        "Eg of a website the problem applies to - "
        "https://fontmellmagnavillagehall.co.uk/",
        "topic": "Performance and connectivity > Site breakages > Web compatibility",
    },
    {
        "question": "I can not open a certain website form my desktop.\r\n"
        "I can if I am using my laptop.\r\n"
        "\r\n"
        "The site I am trying to connect to is elsemanarioonline.com",
        "topic": "Performance and connectivity > Site breakages",
    },
    {
        "question": "I don't know what is happening, but for the last few weeks my "
        "Firefox has been freezing on me, I know the cause is not the "
        "website(s) because I can browse them fine with other browsers, "
        "also when it freezes it won't let me close it, I even tried to "
        "close it using Task Manager, but I get an Access Denied when I "
        "click End Task, so I have to restart my PC.\r\n"
        "\r\n"
        "Any ideas qhat can be happening?",
        "topic": "Performance and connectivity > Crashing and slow performance > App "
        "responsiveness",
    },
    {
        "question": "I can't login to Topcashback.co.uk it just hangs at the login. "
        "this has now been going on for a couple of months, I assume "
        "something has changed with Firefox as I never had a problem "
        "before.\r\n"
        "I have no problems with other browsers (Microsoft Edge or "
        "Chrome)\r\n"
        "I have tried clearing the cache",
        "topic": "Performance and connectivity > Site breakages > Web compatibility",
    },
    {"question": "i have a problem with netflix", "topic": "Undefined"},
    {
        "question": "win10 last FireFox, how migrate all open tabs from one computer "
        "to another\r\n"
        "I cant find clear instruction or video, all they are old and "
        "mention about menu part which my vercion does not have.",
        "topic": "Backup, recovery, and sync > Recover data > Sync and backup " "confusion",
    },
    {
        "question": "I tried to put my name in to tiketmaster passwords and the "
        "whole lot got wiped off!",
        "topic": "Undefined",
    },
    {
        "question": "I updated my FireFox. In the old version I have a list of "
        "bookmarks on the left side on my firefox home screen. In this "
        "new version I dont have that and can't see how to get it back. "
        "Can someone help.\r\n"
        "Also, when someone replies where do I see the reply?",
        "topic": "Browse > Bookmarks",
    },
    {
        "question": "Can't log in to spectrum.net. I called Spectrum. They had me "
        "clear cache. I also Closed out of Firefox and logged back in. "
        "Still couldn't log into Spectrum. Tried to log in using Google "
        "Chrome and was successful. Why can't I log in using Firefox, my "
        "default browser?",
        "topic": "Performance and connectivity > Site breakages > Web compatibility",
    },
    {
        "question": "78 - years old man wants to 1) get rid of several addresses in "
        "the meny row   2) Put icons of my most used programs on the "
        "screen    3) Remove YAHOO from my android",
        "topic": "Settings > Customization > Browser appearance",
    },
    {
        "question": "With the recent Firefox update to my MSI 64-bit Windows 11 "
        "laptop I added the Dark theme extension and enabled it. Now my "
        "task bar, tab bar, bookmarks, and all the other previous "
        "customization is gone! I cannot access Settings or Menu or "
        "anything that will let me customize the home page. Is this a "
        "problem with the dark theme or with the Firefox update? How can "
        "I fix this?",
        "topic": "Backup, recovery, and sync > Recover data",
    },
    {
        "question": "Trying to search on Firefox is now 70% impossible. Keep getting "
        "error code: \r\n"
        "Secure Connection Failed\r\n"
        "\r\n"
        '"An error occurred during a connection to www.google.com. '
        "PR_CONNECT_RESET_ERROR\r\n"
        "\r\n"
        "Error code: PR_CONNECT_RESET_ERROR\r\n"
        "\r\n"
        "    The page you are trying to view cannot be shown because the "
        "authenticity of the received data could not be verified.\r\n"
        "    Please contact the website owners to inform them of this "
        'problem."\r\n'
        "\r\n"
        "What is going on with this? I even get this code when I try to "
        "search on how to reset ALL settings back to factory "
        "default. \r\n"
        "What can be done??",
        "topic": "Performance and connectivity > Error codes",
    },
    {
        "question": "Why are all of my devices syncing, but one?",
        "topic": "Backup, recovery, and sync > Sync data > Sync failure",
    },
    {
        "question": "Is virus protection available with mozilla?'''",
        "topic": "Privacy and security",
    },
    {
        "question": "Within the last week, my homepage has changed in look and "
        "operation.  It no longer has all of my bookmarks, I can no "
        "longer navigate back to my homepage from other sites, etc.  "
        "Also, it have a very plain, sterile display.  What changed and "
        "how to I get back to my original homepage?",
        "topic": "Browse > Home screen",
    },
    {
        "question": "Hi all. I recently did a manual clear of cookies and "
        "afterwards, I've seen two strange issues pop up. \r\n"
        "\r\n"
        "The first was while I was booking hotels on Expedia, it would "
        "not allow me to complete the booking where earlier in the same "
        "day it did. It would simply do nothing when I clicked the final "
        "button. I swapped over to chrome and it worked totally fine, so "
        "it was not the sites issue. \r\n"
        "\r\n"
        "\r\n"
        "The other is in images. I will do an image search, and "
        "typically on the big wall of thumbnails, if you click one, it "
        "will have a preview of the image at a larger size and the link "
        "to the source site, but now it does nothing if I click the "
        "image, and I have to right click and opening in new tab to use "
        "the image to go to the site. This can be temporarily fixed by "
        "clicking the padlock in the address bar, clearing cookies on "
        "the site and reloading, but then as soon as I do a new image "
        "search, it's back to the unresponsive clicks. \r\n"
        "\r\n"
        "I have ublock origins plugin and Malwarebytes browser guard "
        "running,but have never had an issue due to those before and "
        "made no changes with them. Embedded video still works totally "
        "fine, it's only online purchases and image search that I've "
        "seen problems. \r\n"
        "\r\n"
        "I have cleared cookies manually before without this issue. I "
        "have refreshed the installation and it has not fixed it. I'm "
        "really not sure what got knocked loose, but I am sure that is "
        "when things got weird on me.",
        "topic": "Performance and connectivity",
    },
    {
        "question": "I previously was able to open my gmail account with my passkey "
        "or password; now I cannot open, it starts loading and it stops "
        "and never opens. What can I do.",
        "topic": "Performance and connectivity > Site breakages",
    },
    {"question": "how do I uninstall firefox", "topic": "Installation and updates > Install"},
    {
        "question": "All my data seems to have disappeared. I have no browser "
        "history, and all my bookmarks are gone. the only browser "
        "history shows when I started looking for the lost data, "
        "anything before that is gone. please help",
        "topic": "Backup, recovery, and sync > Recover data",
    },
    {
        "question": "Hello,\r\n"
        "Win11 Pro 24H2\r\n"
        "Firefox 136.0.2 (64-bit)\r\n"
        "\r\n"
        "When I alt tab over to my firefox windows and then press ctrl t "
        "to open a new tab it does not work most of the time.\r\n"
        "I have to sit and hit the keys 10-20 times before it will allow "
        "me to open a new tab.\r\n"
        "Do you have any idea why this is happening?\r\n"
        "I have tried safe mode with firefox and the issue persists so "
        "it is definitely not any extension that I run.",
        "topic": "Browse > Tabs",
    },
    {"question": "I need to deal with power point window within team", "topic": "Undefined"},
    {
        "question": "A hacker opened an Instagram account using my gmail account  "
        "([edited] @gmail.com) and the scam Instagram account "
        "(Virgobusch) caused Meta to permanently suspend my Gloria "
        "Waslyn and my Parrots For Peace facebook accounts. I understand "
        "the Virgobusch Instagram published music without royalties or "
        "permission. This was NOT ME. Please restore my Facebook and all "
        "Meta accounts that may be impacted. I originally sent a message "
        "of appeal when it was taken down and that was nearly 1000 days "
        "ago. I have 11 days left to resolve this. Please help. [edited "
        "email and phone# from public community support forum].",
        "topic": "Undefined",
    },
    {
        "question": "What password do I use to allow things like software updates "
        "and other system operations?",
        "topic": "Undefined",
    },
    {
        "question": "I need someone to phone me to got step by step to stop tabs "
        "from loading. I see the answer but I am not a computer guru so "
        "need someone to assist me step by step to stop all my "
        "historical tabs from loading.",
        "topic": "Browse > Tabs",
    },
    {"question": "How to enable Javascript script", "topic": "Settings"},
    {"question": "'''bold text'''how to recover to earlier session", "topic": "Browse > History"},
    {
        "question": "its not working for me...why is that?",
        "topic": "Undefined",
    },
    {
        "question": "I cannot install Adobe Acrobat.     I believe it is because my "
        "computer is old....\r\n"
        "I signed up for the account but will not be able to use it.  I "
        "wish to uninstall...please\r\n"
        "\r\n"
        "Nancy  Howard\r\n"
        "[edited email and phone# from public community support forum]",
        "topic": "Undefined",
    },
    {
        "question": "tell me the steps",
        "topic": "Undefined",
    },
    {
        "question": "Apologies, I have to write this on mobile because among other "
        "pages Firefox will not open for me now, THIS IS ONE OF THEM. "
        "Google is a black square (opens fine in chrome). So are "
        "multiple other pages. I can open new tabs, but clicking on them "
        "to actually navigate to them does nothing. Has anyone else had "
        "this problem???? I don't want to go back to chrome but Firefox "
        "is completely unusable right now.",
        "topic": "Performance and connectivity",
    },
    {"question": "Allowing double-clicking in Firefox", "topic": "Undefined"},
    {
        "question": "Since your last upgrade, I have been able to get into any sites "
        "using CloudFlare security. Prior to that I had no problems at "
        "all. I have tried closing extensions and or clearing cookies. I "
        "especially want access to my banking account. How can I disable "
        "whatever was added to effect CloudFlare?\r\n"
        "CloudFlare either continues to cycle, or gives an error "
        "message.",
        "topic": "Performance and connectivity > Site breakages > Security software",
    },
    {
        "question": "Some time this year I noticed that when I get home from work "
        "and wake up my monitor (PC is always on and doesn't sleep or "
        "log out) I get an email notification in the bottom right corner "
        "for every email I received that day and it takes a couple of "
        "minutes to clear.\r\n"
        "\r\n"
        "I don't remember this before, it was only live notifications in "
        "the bottom right as they came in, if you clicked the Windows "
        "notification icon it would show you all of the past "
        "notifications on the list of course.\r\n"
        "\r\n"
        "I still want the notifications for live incoming mail but not "
        "all of the unread emails previously.\r\n"
        "\r\n"
        "I don't know if this is a Firefox setting or a Windows one but "
        "I couldn't figure out how to change without disabling "
        "notifications all together.",
        "topic": "Undefined",
    },
    {
        "question": "Hi Support Team,\r\n"
        "The firefox addons were disabled after connecting to "
        "internet.\r\n"
        "Could you please let me know the reason for this.\r\n"
        "\r\n"
        "\r\n"
        "Thank you",
        "topic": "Settings > Add-ons, extensions, and themes > Extensions",
    },
    {
        "question": "'''bold text'''I need help with my Firefox browser:  When i go "
        "to home page it shows firefox but when I go to put my\r\n"
        "sight into the browser it shows as GOOGLE search instead of "
        "Firefox.  I am wanting to get as far away from Google \r\n"
        "as possible.  Thank you ahead of ti,e for any help.",
        "topic": "Search, tag, and share > Search",
    },
    {
        "question": "How do I clear cash?  Thought it was listed , but no longer see it?",
        "topic": "Browse > History > Cookies",
    },
    {
        "question": "My Firefox Video Downloader is not showing up. It just has a "
        "gray image in the corner on YouTube.",
        "topic": "Settings > Add-ons, extensions, and themes > Extensions",
    },
    {
        "question": "Wasted a lot of my time trying to figure out California DMV "
        "registration renewal in firefox. Would not complete "
        "transaction. Forced to use chrome instead. So, why should I "
        "continue firefox if I'm being forced to use chrome?",
        "topic": "Performance and connectivity > Site breakages > Web compatibility",
    },
    {
        "question": "Dear Firefox Add-ons Team,\r\n"
        "\r\n"
        "I hope this email finds you well.\r\n"
        "\r\n"
        "We have noticed that the review process for Firefox extensions "
        "is significantly slower compared to other browsers. For "
        "instance, Chrome and Edge typically complete their review "
        "within two hours, whereas Firefox takes considerably longer.\r\n"
        "\r\n"
        "When issues arise with our extension, we need to release an "
        "updated version as soon as possible. Sometimes, these "
        "situations are urgent, and the prolonged review time makes it "
        "difficult to provide users with the latest fixes and "
        "improvements promptly. This delay negatively impacts the user "
        "experience.\r\n"
        "\r\n"
        "We kindly request that you consider optimizing the review "
        "process to help developers deliver timely updates and ensure a "
        "smoother experience for Firefox users.\r\n"
        "\r\n"
        "Thank you for your time and support. We appreciate your efforts "
        "in maintaining the Firefox ecosystem.\r\n"
        "\r\n"
        "Best regards,\r\n"
        "Coupert Development Team",
        "topic": "Settings > Add-ons, extensions, and themes > Extensions",
    },
    {
        "question": "i have checked open previous windows and tabs but every time i "
        "exit and reopen browser it is the default home page opens. I "
        "have unchecked delete cookies option exit also.",
        "topic": "Browse > History",
    },
    {
        "question": "My computer was not used for awhile and neither was my HP "
        "Printer. In the meantime I got a new internet provider with a "
        "new password.  My Dell computer asked for and connected to the "
        "new internet immediately.  Now I am trying to connect the "
        'printer and it tells me "no internet connection." and I can\'t '
        "figure out how to change the connection/password or what I need "
        "to do. I will appreciate any and all help.",
        "topic": "Undefined",
    },
    {
        "question": "I am trying to use Fire Fox as my default browser?",
        "topic": "Settings > Customization",
    },
    {
        "question": "After usual PC restart non of my logins work anymore. I have "
        "logins.json file and key4 db file in my profile but firefox "
        "does not want to read them anymore. In json file I can see all "
        "the website and encrypted passwords, so all looks good there. "
        "Even more interesting, if I create new password it is saved in "
        "the same logins.json file but I can see those in the browser. "
        "So out of 50 logins there I can see only most recent two.\r\n"
        "\r\n"
        "I tried to uninstall and reinstall mozilla and then copy "
        "logins.json and key4 files to the new profile but it did not "
        "help. Any ideas appreciated.",
        "topic": "Backup, recovery, and sync > Recover data",
    },
    {
        "question": "Hello \r\n"
        'So In the "update" i skipped some of the boxes and I realize i '
        "should have NEVER skipped it.\r\n"
        "tho I Still would like to get all my bookmarks back please.",
        "topic": "Backup, recovery, and sync > Recover data",
    },
    {
        "question": "I'm having trouble with my bookmarks. I accidently included "
        "Firefox when using a program to clean up files from my PC. It "
        "wiped my bookmarks but I've managed to locate the backup html "
        "in my profile folder. Unfortunately I can't find anyway to "
        "actually use that back up. All of the guides I've found take "
        "you through the manage bookmarks tab but everything there is "
        "baisically unresponsive for some reason.",
        "topic": "Backup, recovery, and sync > Recover data",
    },
    {
        "question": "Firefox sabotages MeWe.com \r\n" "You may help by firing those responsible.",
        "topic": "Performance and connectivity > Site breakages",
    },
    {
        "question": "Dark Mode is blocked on "
        "https://support.mozilla.org/en-US/questions/ . \r\n"
        "You may help by either allowing add-ons to run or by providing "
        "your own dark mode.",
        "topic": "Settings > Add-ons, extensions, and themes > Extensions",
    },
    {
        "question": "Recently my AdBlocker extension in Firefox was disabled. At "
        "first I thought it was just a bug, but after I closed and "
        "restarted Firefox, it was still disabled, installing various "
        "other ad blocking extensions was thwarted by Firefox claiming "
        "these extensions are corrupt! I tried other approaches, "
        "including installing from github and from third party extension "
        "library; all are stopped by Firefox. I checked Firefox update, "
        "it claims that the latest version I can upgrade to is v127 (I'm "
        "using v126), so I think it's not due to Firefox not up to "
        "date.\r\n"
        "I spent a lot of time figuring these out, most pointing to "
        "Firefox banning Chinese users from using ad blocking "
        "extensions. \r\n"
        "After all these frustrations, I updated Firefox to v127, "
        "thinking updating to the latest version won't hurt, and these "
        "extensions are still disabled, installing ad blocking extension "
        "is still not successful. But somehow I checked whether I'm "
        "using the latest version, and BAM, I can now upgrade to v136. "
        "After the update, all these problems were solved.\r\n"
        "IF ONLY Firefox can provide some useful info of why my "
        "extension is now disabled, and why installing extensions are "
        "not successful, it would save me a lot of time and trouble. You "
        "dumb lazy people!",
        "topic": "Settings > Add-ons, extensions, and themes > Extensions",
    },
    {
        "question": "Secure Connection Failed\r\n"
        "\r\n"
        "An error occurred during a connection to www.nidw.gov.bd. "
        "PR_CONNECT_RESET_ERROR\r\n"
        "\r\n"
        "Error code: PR_CONNECT_RESET_ERROR\r\n"
        "\r\n"
        "    The page you are trying to view cannot be shown because the "
        "authenticity of the received data could not be verified.\r\n"
        "    Please contact the website owners to inform them of this "
        "problem.",
        "topic": "Performance and connectivity > Error codes",
    },
    {"question": "ither email and gmail messing", "topic": "Undefined"},
    {
        "question": "Is there any setting that allows to get rid from this annoying "
        "Titlebar (line with buttons) in fullscreen mode? So that it "
        "never shows up even when hovering the mouse pointer over the "
        "top edge of screen. When it jumps out everything slides down "
        "and always leads to miss clicks when I try to select tabs. I "
        "don't want it to be constantly present here as well because it "
        "takes up screen space.",
        "topic": "Settings > Customization > Browser appearance",
    },
    {
        "question": "i need the option for refresh . i have a lot of problems with "
        "youtube\r\n"
        "u want to clear it i need a good youtube",
        "topic": "Undefined",
    },
    {
        "question": "I can sign on to zoom but I get a message to say that my "
        "Browser is not allowing my microphone or video to be "
        "displayed.  I have used zoom for a number of years and never "
        "had this issue before",
        "topic": "Privacy and security > Security > Device permissions",
    },
    {
        "question": "i cant do anything, i cant bookmark my tabs on the sidebar and "
        "etc. what do i even do?",
        "topic": "Undefined",
    },
    {
        "question": "Im locked out of my sync. I thought i had the pass word saved "
        "away but now iv spent over 24 hour combing old pass words to "
        "try and get it write. some please help me.",
        "topic": "Passwords and sign in > Reset passwords",
    },
    {
        "question": "Bought a new monitor which is set to 3840 x 2160 by default, so "
        "i had to change the Windows UI display setting to 200% for my "
        "eyes.\r\n"
        "\r\n"
        "This is fantastic on Windows and works as expected with Chrome "
        "and Edge browsers. Type appears to be correctly anti-aliased. "
        "It does not work with firefox, however. Both the browser UI and "
        "viewport content is pixelated.\r\n"
        "\r\n"
        "Attached are three examples of the pixelation on text that we "
        "are seeing. \r\n"
        "\r\n"
        "There is no scaling set within the browser - this is a new "
        "install with everything set to default at 100%.\r\n"
        "\r\n"
        "Is there a system setting that we need to invoke in order to "
        "smooth type within the viewport. There are several articles on "
        "this forum that seem to touch on type smoothing but we were "
        "looking to confirm whether there is a default setting that can "
        "be changed outright.",
        "topic": "Settings > Customization > Browser appearance",
    },
    {
        "question": "When I visit certain websites, I get the web site selection "
        "text over the top of the regular selection text (see image).  "
        "Not sure if this is a MS issue of a Firefox Issue.",
        "topic": "Undefined",
    },
    {
        "question": "After a recent update to FireFox, every time I click the puzzle "
        "icon to try and Pin an extension to the Toolbar it takes me to "
        "`about:addons` instead. In `about:addons` I cannot click or "
        "right-click anything and select Pin To Toolbar as I was once "
        "able to.\r\n"
        "\r\n"
        "I have downloaded FireFox Developer Edition and the puzzle icon "
        "does exactly what it suppoused to do which is to show a "
        "DropDown list of installed extensions I can Pin or Un-Pin.\r\n"
        "\r\n"
        "'''Looks like a bug.'''\r\n"
        "\r\n"
        "Why is this happening? Please tell me that's not intentional.",
        "topic": "Settings > Customization",
    },
    {
        "question": "It looks awful and really ruins the user experience. I've "
        "attached a picture.",
        "topic": "Settings > Customization > Browser appearance",
    },
    {
        "question": "I want to watch Survivor on cbs.com.  I get error code 111.  It "
        "will not load.  Something is blocking.  How do I unlock?",
        "topic": "Performance and connectivity > Error codes",
    },
    {
        "question": "How to update my Metamask",
        "topic": "Settings > Add-ons, extensions, and themes > Extensions",
    },
    {
        "question": "Firefox says it can't verify my PayPal app. I am pretty darn "
        "sure I have the legit app, so ???",
        "topic": "Privacy and security",
    },
    {"question": "normal setting recovary", "topic": "Backup, recovery, and sync > Recover data"},
    {
        "question": "When typing in my email address, Firefox automatically "
        "completes the name. My name was mispelled once and now it "
        "appears every day. How do I delete this?\r\n"
        "\r\n"
        "Thank you.",
        "topic": "Settings > Autofill",
    },
    {
        "question": "installed on new W11 dell. Get no sound from youtube or Tubi. "
        "all other sound sources that i have tried work ok",
        "topic": "Browse > Audio and Video",
    },
    {
        "question": "how to stop Application error: a client-side exception has "
        "occurred while loading www.yahoo.com (see the browser console "
        "for more information).",
        "topic": "Performance and connectivity > Site breakages",
    },
    {"question": "set home page", "topic": "Browse > Home screen"},
    {"question": "how to set home page", "topic": "Browse > Home screen"},
    {
        "question": "Dear Firefox Team,\r\n"
        "I would like to ask you to consider updating Firefox for "
        "Windows desktop computers. I appreciate the innovative "
        "solutions introduced in your products, so I would like to "
        "propose adding a new functionality to the browser's home "
        "page.\r\n"
        "I propose implementing the option of displaying news directly "
        "on the home page. Users could easily select news categories "
        "that interest them, which would allow for better "
        "personalization of the presented content. What's more, it would "
        "be possible to set the refresh rate of the displayed news - for "
        "example, every 3, 5 minutes or at any selected time "
        "intervals.\r\n"
        "\r\n"
        "I am convinced that such a feature would significantly increase "
        "the usability of the browser and could attract more users who "
        "expect quick and personalized information on a daily basis.\r\n"
        "\r\n"
        "Thank you for your time and for considering my proposal. I hope "
        "that future releases of Firefox will find a place for this "
        "innovative functionality.",
        "topic": "Browse > Home screen",
    },
    {
        "question": "I inputed my proxy setting and tried going on a website but it "
        "keeps saying ‘the proxy server is refusing connections’",
        "topic": "Performance and connectivity > Site breakages > Security software",
    },
    {
        "question": "It seems that something has gone awry with adding new shortcuts "
        "and/or bookmarks. \r\n"
        "Any one have a solution yet?",
        "topic": "Browse > Bookmarks",
    },
    {
        "question": "somehow the tabs are suddenly on the left side in vertical "
        "order not on top in horizontal order. Please help.",
        "topic": "Browse > Tabs",
    },
    {
        "question": "As the subject says and the issue being there seems to be no "
        'info regarding what "helper" is being installed !\r\n'
        "\r\n"
        "I'm on macOS Big Sur and the update does not finish if admin "
        "password is not given...\r\n"
        "\r\n"
        "So, what helper is it ?\r\n"
        "\r\n"
        "Did I miss something (quite possible although I made several "
        "attempts) ?\r\n"
        "\r\n"
        "Thanks in advance!",
        "topic": "Installation and updates > Install",
    },
    {
        "question": "How do I get this platform installed?",
        "topic": "Installation and updates > Install",
    },
    {
        "question": "I am tired of this bullshit.\r\n"
        "\r\n"
        "So i was using the beta branch of the firefox and beta version "
        "stopped working with a site for some time. so i tried to come "
        "back to the stable version. \r\n"
        "\r\n"
        "After i do that and fix my config. In every couple of hours "
        "there would be a notification window pop up with sound saying "
        "this \r\n"
        "\r\n"
        '"firefox this profile was last used with a newer version of '
        'this application. Please create a new profile"\r\n'
        "\r\n"
        "So i did create a new profile BUT i copy pasted my own "
        "configuration.UI stuff from my old settings from "
        '"About:config"\r\n'
        "\r\n"
        "This notification STILL comes up FFS what do i need to do "
        "then? \r\n"
        "\r\n"
        "HOW COME MY UI CONFIGURATION TRIGGERS THE DAMN NOTIFICATION?\r\n"
        "\r\n"
        "I will not re-do my fckng UI configuration by hand.",
        "topic": "Accounts > Profiles",
    },
    {
        "question": "Hello, I have some issues with Firefox keeping my logged in my "
        "Google account. When I close Firefox it logs me out of Google, "
        "but not other websites. I have tried some methods from other "
        "threads on this site but still without success. I have the "
        "setting for delete cookies on Firefox close to off and have "
        "tried Firefox remember history and use custom settings. Thank "
        "you for reading this.",
        "topic": "Browse > History > Cookies",
    },
    {"question": "I need to reset default apps, but can't find it", "topic": "Settings"},
    {
        "question": "I have a couple questions on tab groups, I'm a new ms edge "
        "refuge but this not as smooth as I would like :).\r\n"
        "I realize tab groups are oddly new for FF, but I'm trying to "
        "get setup and running into two main issues.\r\n"
        "1. I cant seem to freely reorder the tab groups, I can move the "
        "individual book pages no problem but not the groups as a whole. "
        "I would expect to be able to left hold click drag the order of "
        "the groups just like individual tabs.\r\n"
        "2. Tab groups don't seem to exist across clients (or maybe I'm "
        "missing the how). If I open FF on my mac I would expect to see "
        "or at least be able to reopen the same tab groups as my windows "
        "PC, not just the individual pages from history on other device. "
        "Is there a way to do this?\r\n"
        "3. can't import tab groups from edge? You don't want to make it "
        "easy for folks to switch?\r\n"
        "\r\n"
        "Thanks, if I missed something happy to learn.",
        "topic": "Browse > Tabs",
    },
    {"question": "how do i update firefox", "topic": "Installation and updates > Update"},
    {"question": "How to allow pop ups", "topic": "Settings"},
    {
        "question": "When i try to drag a text/word/link to between tabs (i "
        "generally have 10 tabs open) it opens a new tab at the far "
        'right. I tried to change "browser.tabs.insertAfterCurrent" but '
        "it just opens the new tab next to the tab that i'm viewing. For "
        "example, when i'm at the sixth tab and i want to open a new tab "
        "(by dragging) between third and fourth tabs it opens that tab "
        "on the far right. This wasn't like that before how can i change "
        "it?",
        "topic": "Browse > Links",
    },
    {
        "question": "She  denied permission to install helper at first, but that "
        "caused firefox to be\r\n"
        "dysfunctional.  Retrying the install and giving permission to "
        "install the helper\r\n"
        "did not correct the problem.  Her laptop is pretty much down "
        "for the count\r\n"
        "on this problem - firefox does not come up.  Endless spinning "
        "beachball. \r\n"
        "\r\n"
        "Is a work-around available?\r\n"
        "\r\n"
        "It seems there is some conflict between the firefox helper and "
        "her VPN,\r\n"
        "private internet access (PIA) adding the login background "
        "task.  She's. been using\r\n"
        "PIA for years.\r\n"
        "\r\n"
        "I would try removing and re-installing firefox as a work-around "
        "but that would\r\n"
        "destroy the her bookmarks she relies on.\r\n"
        "\r\n"
        "Thanks, Jerry",
        "topic": "Installation and updates > Install > Install failure",
    },
    {
        "question": "I have tried the fixes. None of them work and I cannot access "
        "profile manager. I would like to chat or speak to a "
        "representative. Thank you.",
        "topic": "Performance and connectivity > Crashing and slow performance > "
        "Launch failure",
    },
    {
        "question": "There is an issue with PDFs downloaded using the Firefox PDF "
        "viewer. The PDF contains a valid digital signature.\r\n"
        "When I set the parameter pdfjs.disabled = true, everything "
        "works as expected, the PDF is downloaded correctly, and when I "
        "open it with Adobe Reader, the signature is valid.\r\n"
        "However, when I set this parameter to false (default value) and "
        "download the PDF using the built-in Firefox PDF viewer, the "
        "signature becomes invalid.\r\n"
        "I compared both PDF files using a text editor and a diff tool, "
        "and the only difference I found was a specific change in the "
        "content.\r\n"
        "1)pdf- signature is valid\r\n"
        "\uf8fbΨ\uf8fbα Exif  II*            \uf8fbμ Ducky      d  "
        '\uf8fbα  http://ns.adobe.com/xap/1.0/ <?xpacket begin="ο»Ώ" '
        'id="W5M0MpCehiHzreSzNTczkc9d"?> <x:xmpmeta '
        'xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 5.6-c138 '
        '79.159824, 2016/09/14-01:09:01        "> <rdf:RDF '
        'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"> '
        '<rdf:Description rdf:about="" '
        'xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/" '
        'xmlns:stRef="http://ns.adobe.com/xap/1.0/sType/ResourceRef#" '
        'xmlns:xmp="http://ns.adobe.com/xap/1.0/" '
        'xmpMM:DocumentID="xmp.did:FF61BC20787811E896E6E83BD502C18A" '
        'xmpMM:InstanceID="xmp.iid:FF61BC1F787811E896E6E83BD502C18A" '
        'xmp:CreatorTool="paint.net 4.0.16"> <xmpMM:DerivedFrom '
        'stRef:instanceID="452A56456B1E68A148301EBAD51349D5" '
        'stRef:documentID="452A56456B1E68A148301EBAD51349D5"/> '
        "</rdf:Description> </rdf:RDF> </x:xmpmeta> <?xpacket "
        'end="r"?>\uf8fbξ Adobe dΐ   \uf8fbΫ '
        "„                                                            "
        "\uf8fbΐ  F F   \uf8fbΔ •               \t \r\n"
        "2)invalid pdf\r\n"
        "\uf8fbΨ\uf8fbα Exif                  \uf8fbμ Ducky      d  "
        '\uf8fbα  http://ns.adobe.com/xap/1.0/ <?xpacket begin="ο»Ώ" '
        'id="W5M0MpCehiHzreSzNTczkc9d"?> <x:xmpmeta '
        'xmlns:x="adobe:ns:meta/" x:xmptk="Adobe XMP Core 5.6-c138 '
        '79.159824, 2016/09/14-01:09:01        "> <rdf:RDF '
        'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"> '
        '<rdf:Description rdf:about="" '
        'xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/" '
        'xmlns:stRef="http://ns.adobe.com/xap/1.0/sType/ResourceRef#" '
        'xmlns:xmp="http://ns.adobe.com/xap/1.0/" '
        'xmpMM:DocumentID="xmp.did:FF61BC20787811E896E6E83BD502C18A" '
        'xmpMM:InstanceID="xmp.iid:FF61BC1F787811E896E6E83BD502C18A" '
        'xmp:CreatorTool="paint.net 4.0.16"> <xmpMM:DerivedFrom '
        'stRef:instanceID="452A56456B1E68A148301EBAD51349D5" '
        'stRef:documentID="452A56456B1E68A148301EBAD51349D5"/> '
        "</rdf:Description> </rdf:RDF> </x:xmpmeta> <?xpacket "
        'end="r"?>\uf8fbξ Adobe dΐ   \uf8fbΫ '
        "„                                                            "
        "\uf8fbΐ  F F   \uf8fbΔ •               \t \r\n"
        "I cannot understand why the Firefox PDF viewer modifies the PDF "
        "content.\r\n"
        "This is happening only to version 136.0.2. I had no issue "
        "before this version.\r\n"
        "Could you please help me?",
        "topic": "Browse > Images and documents > PDFs",
    },
    {
        "question": "How can I get FireFox to open a webpage on a website on my "
        "LAN.\r\n"
        "\r\n"
        "Chrome has same problem.  \r\n"
        "\r\n"
        "Safari gets to the webpage fine.\r\n"
        "\r\n"
        "Please see attached image",
        "topic": "Performance and connectivity > Site breakages > Web compatibility",
    },
    {
        "question": "I tried to login to my account with my email address, but it "
        "pops out to ask mw to create a new account.\r\n"
        "How wierd is that?!\r\n"
        "I follow the previous registration confirmation email last year "
        "and trace my account.\r\n"
        "I can clearly see that the email address is the one I try to "
        "login with.\r\n"
        "how is that happen?\r\n"
        "can i get my data back?\r\n"
        "\r\n"
        "BTW, I create the recovery key through the website.\r\n"
        "The problem is how I login my account in the APP.",
        "topic": "Accounts",
    },
    {
        "question": "Hi - \r\n"
        "\r\n"
        "I've been using Firefox for 10+ years, and have not touched my "
        "add-ons etc for years. I also regularly clear my cache of temp "
        "files.\r\n"
        "\r\n"
        "That said, searching my (vast) bookmarks in Firefox used to be "
        "lickety-split, very fast. Then, it started slowing down, on "
        "both PC (Windows 10).  Then, a little while later, it started "
        "on my laptop (Macbook with latest IoS). \r\n"
        "\r\n"
        "It's now gotten so bad that I am searching my emails to find "
        "the links I'm looking for, rather than putting my browser into "
        "a coma for a time, because it freezes.\r\n"
        "\r\n"
        "What is the problem, and how do I overcome it?\r\n"
        "\r\n"
        "J",
        "topic": "Performance and connectivity > Crashing and slow performance > App "
        "responsiveness",
    },
    {
        "question": "I create and save files in OneDrive. When I open a file, it "
        "always opens in the Microsoft Edge Browser which is a problem "
        "for the old guy, me. I prefer that they open only in the "
        "documents folder as their specific kind of document; Word, PDF, "
        "and Excel spreadsheet files so that I can then move my files "
        "into various folders and sub-files. Hopefully, someone can "
        "figure out what I have said and help me.\r\n"
        "•\tI'm uncertain if the topic I chose accurately describes my "
        "question.",
        "topic": "Undefined",
    },
    {
        "question": "With the latest update, I can't open my att.net email. Any " "ideas?",
        "topic": "Performance and connectivity > Site breakages",
    },
    {"question": "I forgot my password?", "topic": "Passwords and sign in > Reset passwords"},
    {
        "question": "My LastPass extension has not been showing up in my browser "
        "toolbar. I uninstalled it, reinstalled it, and still nothing. I "
        "can't really go through my workday without this extension and "
        "will need to switch browsers if I can't get this to show up. "
        "Any advice?",
        "topic": "Settings > Add-ons, extensions, and themes > Extensions",
    },
    {
        "question": "ATT.NET is blocking my access to ATT/Yahoo email from my "
        "ATT.net account using Firefox '''''''but not using "
        "Chrome?'''''''\r\n"
        "I have stopped all tracking and cookie blocking\r\n"
        "\r\n"
        "\"Something's gone wrong\r\n"
        "We may be having trouble with your connection. Connecting your "
        "device to Wi-Fi could help fix the issue or try again later.\r\n"
        "If you were using an app, close this page. Otherwise, start "
        'over."',
        "topic": "Performance and connectivity > Site breakages > Web compatibility",
    },
    {
        "question": "The error SEC_ERROR_REVOKED_CERTIFICATE means that the "
        "website's SSL/TLS certificate has been revoked by the "
        "certificate authority (CA). This prevents secure connections "
        "because the certificate is no longer trusted.",
        "topic": "Performance and connectivity > Error codes",
    },
    {"question": "Please unlock the my Facebook ID prince joshya je", "topic": "Undefined"},
    {
        "question": "i reset my primary password. how do i find out what it is?",
        "topic": "Passwords and sign in > Primary password",
    },
    {
        "question": "Firefox does not save manually inputted password/user id "
        "information from the web login page.  It does if entered into "
        "password section in Firefox.  I've checked the box under saved "
        "passwords but does not do anything.  I used to be able to enter "
        'login information & PW and Firefox would ask "Do you want to '
        'save this PW?..."This would build the PW file.  But, the only '
        "way I can do this is to manually enter data in the Mozilla "
        "application menu.  What's wrong?\r\n"
        "thanks",
        "topic": "Passwords and sign in > Save passwords > Password manager",
    },
    {
        "question": "I had a website that possibly phished me in my Firefox "
        "browser.  I was in a webpage, and I had a full screen McAfee "
        "notification for a possible malware and asked to start a scan.  "
        "I wasn't fully realizing what was happening and I did so.  I "
        "was able to get out of the full screen mode and realized it was "
        "the webpage I was on but wasn't the same page I had been on "
        "previously. I started getting security popups as if Microsoft "
        "was issuing them, but I couldn't close them, and they all had "
        "links to follow.  I killed the internet connection, tried "
        "repairing Firefox and still got the pop ups.  So, I uninstalled "
        "Firefox and that stopped the popups.  Can you tell me if there "
        "are any current security vulnerabilities with Firefox and can "
        "you tell me if there is a record of what my Firefox browser "
        "downloaded and installed on my computer?",
        "topic": "Privacy and security > Security > Browser security",
    },
    {
        "question": "I'm attempting to set up Firefox in a newly installed OS and "
        "have logged into my Sync account.  Many aspects seem to be "
        "loaded in, but the status via the Settings is stuck at "
        '"Syncing..." despite waiting several hours.  Quitting Firefox '
        "results in a crash window popping up.\r\n"
        "\r\n"
        "There are no files in the weave/logs directory.  The "
        "weave/failed directory has multiple json files; most almost "
        "completely empty.  addons.json has an ID, but that's pretty "
        "much it.\r\n"
        "\r\n"
        "Deleting the .mozilla directory and starting over yielded no "
        "change in behavior.\r\n"
        "\r\n"
        "Any help would be appreciated.  Thank you.",
        "topic": "Backup, recovery, and sync > Sync data > Sync failure",
    },
    {
        "question": "my personal email login for my (ATT email) is requesting a piv "
        "card and I don't use one.",
        "topic": "Undefined",
    },
    {
        "question": "I can no longer switch search engines via the pull down list "
        "available to the right of the search bar. I used to be able to "
        "switch from a list I set up in settings. I now have to go into "
        "settings to change my search engine.  This is annoying.\r\n"
        "Also, recently, when I make my first search with Google Search "
        "I have to enter the search criteria twice.  The first time the "
        "system just sits there with no response. The second time it  "
        "responds normally.\r\n"
        "This is the same on both of my Dell Lattitude laptops running "
        "the latest version of Windows 11.\r\n"
        "I run NORD VPN and Trend Micro internet security",
        "topic": "Search, tag, and share > Search",
    },
    {
        "question": "I have two monitors:\r\n"
        "Monitor 1 is Asus PG248QP(Run in 1920 x 1080 360hz landscape "
        "100% scale)\r\n"
        "Monitor 2 is G272U Pro(Run in 4320 x 2160 60hz landscape 150% "
        "scale).\r\n"
        "I arrange them veritcally, monitor 2 on top and monitor 1 at "
        "the bottom.\r\n"
        "\r\n"
        "When I minimize the non-fullscreen firefox window on the "
        "monitor 1, black/transparent border shows on the left, right, "
        "and bottom of the firefox window.\r\n"
        "\r\n"
        "When I arrange two monitor horizontally, everything normal. I "
        "place monitor 1 at the left of monitor 2.\r\n"
        "\r\n"
        "When I do this on the monitor 2, everything normal.\r\n"
        "\r\n"
        "I have to use two monitors vertically, since I don't have much "
        "space.\r\n"
        "\r\n"
        "I also tried different versions of firefox. for now, 129.0 to "
        "136 has these problems. I have install chrome, brave, edge. "
        "None of them has this problem.\r\n"
        "\r\n"
        "windows 11 23h2 (22631.5039)\r\n"
        "cpu: 13900k\r\n"
        "gpu: 4090 with 572.60\r\n"
        "ram: 32gb x 2\r\n"
        "\r\n"
        "Firefox 137.0\r\n"
        "\r\n"
        "already tried refresh firefox profile.",
        "topic": "Settings > Customization > Browser appearance",
    },
    {
        "question": "When shutting down the computer through the OS, Firefox closes "
        "each window separately instead of quitting (e.g. with Ctrl+Q). "
        "Windows with multiple tabs ask for confirmation, stopping or "
        "delaying the shutdown process, and single tab windows close and "
        "are not restored. I have to manually quit Firefox before "
        "shutting down the computer every time if I want my session to "
        "be correctly restored.\r\n"
        "\r\n"
        "I have been using Firefox for a long time, and remember it "
        "working nicely with shutdown/logout. This issue showed up after "
        "changing my OS, so I believe it must be related to Flatpak, "
        "Fedora, KDE, or a mix of them.",
        "topic": "Performance and connectivity",
    },
    {
        "question": "When attempting to drag/Insert picture into email text, the "
        "message \"The following files couldn't be attached: "
        'filename.jpg.  Please try again later." appears.  I have not '
        "been able to find a solution.  The dragged/Inserted picture "
        "always ends up outside the email text box and cannot be moved "
        "into it.  What is a solution?\r\n"
        "\r\n"
        "Is this something new or do I need to reload Firefox?  Firefox "
        "133.03 64-bit is up to date on Windows 10.\r\n"
        "\r\n"
        "It worked last Christmas!!!  It is not important now that the "
        "holiday is over but would like to fix it.",
        "topic": "Browse > Images and documents > Images",
    },
    {
        "question": "I have been trying to log in to a newspaper website for which I "
        "have a subscription.  This used to work in Firefox without a "
        "problem, but for a while now I have been encountering the "
        "problem that when I open the website the usual options "
        '"Subscribe" and "Log In" are missing.  The "Log In" option is '
        "available when I open the website in Microsoft Edge.  I have "
        "attached screenshots showing the missing links.\r\n"
        "\r\n"
        "I have tried troubleshooting and opening in Safe Mode to "
        "disable any add-ons but still without success.  I am hoping "
        "that there may be a simple solution and would appreciate any "
        "help.\r\n"
        "\r\n"
        "I am using Windows 11 and Firefox 133.0.3 (64-bit).",
        "topic": "Performance and connectivity > Site breakages > Web compatibility",
    },
    {
        "question": "I turn on my old laptop. After update(about 07.23) I lost my "
        "bookmarks.\r\n"
        "Now I tried to do what you wrote me with profiles, but there is "
        "no profile with my bookmarks. What I can do now??",
        "topic": "Backup, recovery, and sync > Recover data",
    },
    {
        "question": "Hello,\r\n"
        "\r\n"
        "Firefox's advanced tracking protection (strict mode) is known "
        "to cause problems on x.com !\r\n"
        "\r\n"
        "I don't know how to fix the Firfox error.",
        "topic": "Privacy and security > Tracking protection",
    },
    {
        "question": 'I would like to know how to get an "app password" for Firefox '
        "so that I can sync Outlook with Firefox. I received an error "
        "msg that said I needed to get an app password from Firefox in "
        "order to sign in  to Outlook to complete the sync process. Any "
        "help would be greatly appreciated.",
        "topic": "Backup, recovery, and sync > Sync data",
    },
    {
        "question": "Some sites I use will not let me use them unless I stop using "
        "add blocking.  I have not installed an add blocker so I am "
        "thinking it must be one in Firefox. Assuming this is true, how "
        "can I discontinue the add blocker at a specific site so I can "
        "access/read/use its contents. Thank you in advance for any help "
        "you may be able to provide. Ken",
        "topic": "Privacy and security > Tracking protection",
    },
    {
        "question": "How can I use my own photo as wallpaper for Firefox?",
        "topic": "Settings > Customization > Browser appearance",
    },
]


SPAM_EVAL_SUITE_1 = [
    "The first",
    "https://telegra.ph/YOUR-PERSONAL-LINK-02-18-229,1ID-504675588324,UK021928379YP. "
    "Is it real, did I get the from Google. About my crypto mining account and "
    "was any money delivered to them or Google. What it or how do I find my may "
    "account with money in it. I need to access it so I can get off the streets "
    "because I been living in my truck for 2 years now.  I'm trying find a place "
    "to live and it's hard when you don't have any money and you can't access "
    "your investments either",
    "updates",
    "firefox",
    "accessibility",
    "My website’s menu is not displaying correctly in Firefox, while it works "
    "perfectly in Chrome. Some menu items appear misaligned, missing, or "
    "unclickable in Firefox. I have reviewed the CSS and JavaScript but couldn’t "
    "find any major issues. Clearing the browser cache and disabling extensions "
    "did not resolve the problem. I need help identifying the cause and finding a "
    "solution to ensure the menu functions correctly across all browsers.",
    "Icant media peer connection",
    '"Accept the Risk and Continu',
    "My name is Abdussalam Umar Muhammad",
    "* # Bulleted list item",
    "I can bot send email to party. It does not enter into mailbox and does not "
    "show up in Spam",
    "Please Reply",
    "To browse",
    "'''bold text'''",
    "'''''bold text'''''",
    "HOW DO I OPEN QUICKEN TO DO TAX PREPARATION?",
    "Hello Facebook team.    My facebook account was disabled.    About a month "
    "ago my dzable showed up I applied for my account to the team several times "
    "but it didn't help me till today I didn't get access to my facebook account "
    "not even my google account and what about facebook.    Today again I am "
    "entering my account identity I am entering my identity.    Kindly check the "
    "identity and give me the access, also a report is given but no report was "
    "ever given to my account at the airport. I don't know why this report is "
    "given. This report is about nude pictures of underage boys. Unfortunately, I "
    "have never done it. If it is forgotten, please forgive me.  So give me "
    "access to facebook account.    Thank you facebook team my name on facebook "
    "is md [edited] id is [edited] / my riku home email is [edited].    My mobile "
    "number is.    [edited]",
    "https://en.wikipedia.org/wiki/Category:All_portals\r\n"
    "https://en.wikipedia.org/wiki/HTML\r\n"
    "https://www.dropbox.com/scl/fi/1h9h4v2r8lmonww9lq6sa/"
    "torunpostcom.-dropbox.-androidfilesuser_datafilesu1443193667scratchAdminbox-adminbox"
    ".-net-binance_home-k.bancha1989-gmail.com.url?rlkey=i7yf0t3yasr\r\n"
    "S1\r\n"
    "Https:\\\\YouTube.com @bancheakritsanakan_ adminbox_net",
    "https://en.wikipedia.org/wiki/Category:All_portals\r\n"
    "https://www.dropbox.com/scl/fi/1h9h4v2r8lmonww9lq6sa/"
    "torunpostcom.-dropbox.-androidfilesuser_datafilesu1443193667scratchAdminbox-adminbox"
    ".-net-binance_home-k.bancha1989-gmail.com.url"
    "?rlkey=i7yf0t3yasrbycvjaycmj48eb&st=0rl6lmuj&dl=0",
    "[[kahiru Ajihad.v2 |kahiru Ajihad.v2 ]]",
    "[[kahiru]] Kahiruajihad866@gmail.com",
    "yutug",
    "yttttttttttttf",
    "Help Bluetooth",
    "Facebook dissabed or suspended",
    "all time help me",
    "Issue with troubleshooting, all kinds of different problems with everything "
    "I can go down a entire list but that's what happened All night long and it "
    "was the absolute night ruiner and not to mention buzz kill I should have "
    "kept dick down my throat instead of bitch all night lol............ Hehehe "
    "🥰🤤🔥🤤🔥",
    "bbbvvvvv",
    "i want a live video\r\n feed of my location",
    "Change password",
    "Gold colour",
    "please window 10 download",
    "[https://lovemymed.com/product/sibofix/ Sibofix] '''Sibofix''' is designed "
    "to support digestive health by addressing various gastrointestinal concerns. "
    "It works by promoting a balanced gut environment, which can alleviate "
    "symptoms such as bloating, gas, and discomfort. The formulation includes "
    "ingredients that help enhance digestion and nutrient absorption, making it "
    "easier for the body to process food effectively. If you're looking to "
    "improve your digestive wellness, you can conveniently purchase Sibofix at "
    "[https://lovemymed.com Lovemymed] '''lovemymed''', where you’ll find it "
    "readily available for your needs.",
    "I can,t",
    "NIOEN",
    "thanks",
    "اريد تنزيل سحابه",
    "'''bold text'''",
    "[http://+959884397062 venmatman25@gmail.com]",
    "# Numbered list item* 1 download photos from SD",
    "'''cours'''",
    "'''bold text'''",
    "Walmart job warehouse package",
    "Hack tool for me panel use the off chance that you are bhai bhai 😀😉 "
    "eueksgwla me know what time pass key chahiye tha na to padana",
    "jkdgjhtjgfdfxgjky",
    "iamkeith777@gmail.com",
    "Yarukalove5@gmail.com",
    "Hollywood California's",
    "I am to use firefox browser fire securing my facebook accouns'''''''''''bold "
    "text'''''''''''",
    "'''''",
    "I want to register",
    "'''bold text'''",
    "# Numbered list item",
    "''italic text''",
    "Hacked",
    "'''bold text'''",
    "'''Go\r\n'''",
    "01111777370",
    "how are you",
    "[[Knowledge Base Article|chatting ]]",
    "prchonal yous",
    "My profile video photo",
    "[[https://www.facebook.com/share/15rLt58dnW/|https://www.facebook.com/share/15rLt58dnW/]]",
    "ACTION  intertayment Global",
    "Hhjjhvv",
    "'''bold text'''",
    "User ID: _solo_king_93__",
    "I am Ernest Mussah",
    "'''''# * bold text'''''",
    "* Bulleted list item",
    "# * '''''Numbered list item'''''",
    "nandan",
    "tiada yang bermasalah",
    "Find a job  vacancy in Australia",
    "Need to ask a few questions with someone from the Honor a9X brand\r\n"
    "\r\n"
    "''Thread locked due to insufficient information or off topic. For assistance "
    "with a Mozilla product, please submit a new question via [/questions/new] "
    "with complete details. Thanks.''",
    "How is modulus of a basis vector equal to a radius of a curve?",
    "Hello\r\n"
    "\r\n"
    "''Thread locked due to insufficient information. For assistance, please "
    "submit a new question via [/questions/new] with complete details. Thanks.''",
    '"New users at Temu ""Saudi Arabia"" receive a SAR100 discount on orders over '
    'SAR100 Use the code [""ack887223""] during checkout to get Temu ""Saudi '
    'Arabia"" Discount SAR100 off For New Users. You n save SAR100 off your first '
    "order with the coupon code available for a limited time only.\r\n"
    "Extra 30% off for new and existing customers + Up to SAR100 % off & more.\r\n"
    'Temu ""Saudi Arabia"" coupon codes for New users- [""ack887223""]\r\n'
    'Temu ""Saudi Arabia"" discount code for New customers- [""ack887223""]\r\n'
    'Temu ""Saudi Arabia"" SAR100 coupon code- [""ack887223""]\r\n'
    'what are Temu ""Saudi Arabia"" codes- ""ack887223""\r\n'
    'does Temu ""Saudi Arabia"" give you SAR100 - [""ack887223""] Yes Verified\r\n'
    'Temu ""Saudi Arabia"" coupon code January 2025- {""ack887223""}\r\n'
    'Temu ""Saudi Arabia"" New customer offer {""ack887223""}\r\n'
    'Temu ""Saudi Arabia"" discount code 2025 {""ack887223""}\r\n'
    '100 off coupon code Temu ""Saudi Arabia"" {""ack887223""}\r\n'
    'Temu ""Saudi Arabia"" 100% off any order {""ack887223""}\r\n'
    '100 dollar off Temu ""Saudi Arabia"" code {""ack887223""}\r\n'
    'Temu ""Saudi Arabia"" coupon SAR100 off for New customers\r\n'
    "There are a number of discounts and deals shoppers n take advantage of with "
    'the Teemu Coupon Bundle [""ack887223""]. Temu ""Saudi Arabia"" coupon SAR100 '
    'off for New customers""ack887223"" will save you SAR100 on your order. To '
    "get a discount, click on the item to purchase and enter the code. You n "
    "think of it as a supercharged savings pack for all your shopping needs\r\n"
    'Temu ""Saudi Arabia"" coupon code 80% off – [""ack887223""]\r\n'
    'Free Temu ""Saudi Arabia"" codes 50% off – [ack887223]\r\n'
    'Temu ""Saudi Arabia"" coupon SAR100 off – [""ack887223""]\r\n'
    'Temu ""Saudi Arabia"" buy to get BD39 – [""ack887223""]\r\n'
    'Temu ""Saudi Arabia"" 129 coupon bundle – [""ack887223""]\r\n'
    'Temu ""Saudi Arabia"" buy 3 to get €99 – [""ack887223""]\r\n'
    'Exclusive SAR100 Off Temu ""Saudi Arabia"" Discount Code\r\n'
    'Temu ""Saudi Arabia"" SAR100 Off Coupon Code : (""ack887223"")\r\n'
    'Temu ""Saudi Arabia"" Discount Code SAR100 Bundle '
    '""ack887223"")""ack887223""\r\n'
    'Temu ""Saudi Arabia"" SAR100 off coupon code for Exsting users : '
    '(""ack887223"")\r\n'
    'Temu ""Saudi Arabia"" coupon code SAR100 off\r\n'
    'Temu ""Saudi Arabia"" SAR100 % OFF promo code ""ack887223"" will save you '
    "SAR100 on your order. To get a discount, click on the item to purchase and "
    "enter the code.\r\n"
    'Yes, Temu ""Saudi Arabia"" offers SAR100 off coupon code “""ack887223""” for '
    "first time users. You n get a SAR100 bonus plus 30% off any purchase at Temu "
    '""Saudi Arabia"" with the SAR100 Coupon Bundle at Temu ""Saudi Arabia"" if '
    'you sign up with the referral code [""ack887223""] and make a first purchase '
    "of SAR100 or more.\r\n"
    'Temu ""Saudi Arabia"" coupon code 100 off-{""ack887223""}\r\n'
    'Temu ""Saudi Arabia"" coupon code -{""ack887223""}\r\n'
    'Temu ""Saudi Arabia"" coupon code SAR100 off-{""ack887223""}\r\n'
    'kubonus code -{""ack887223""}\r\n'
    'Are you looking for incredible savings on your next Temu ""Saudi Arabia"" '
    'purchase? Look no further! We\'ve got the ultimate Temu ""Saudi Arabia"" '
    "coupon code SAR100 off that will make your shopping experience even more "
    'rewarding. Our exclusive coupon code [""ack887223""] offers maximum benefits '
    "for shoppers in the USA, Canada, and European nations.\r\n"
    'Don\'t miss out on this opportunity to save big with our Temu ""Saudi '
    'Arabia"" coupon SAR100 off and Temu ""Saudi Arabia"" 100 off coupon code. '
    'Whether you\'re a new customer or a loyal Temu ""Saudi Arabia"" shopper, '
    "we've got you covered with amazing discounts and perks.\r\n"
    'What Is The Coupon Code For Temu ""Saudi Arabia"" SAR100 Off?\r\n'
    "Both new and existing customers can enjoy fantastic benefits by using our "
    'SAR100 coupon code on the Temu ""Saudi Arabia"" app and website. Take '
    'advantage of this Temu ""Saudi Arabia"" coupon SAR100 off and SAR100 off '
    'Temu ""Saudi Arabia"" coupon to maximize your savings. Here are some of the '
    'incredible offers you can unlock with our coupon code [""ack887223""]:\r\n'
    '[""ack887223""]: Flat SAR100 off on your purchase\r\n'
    'Temu ""Saudi Arabia"" Coupon Code SAR100 Off For New Users In 2025\r\n'
    "New users can reap the highest benefits by using our coupon code on the Temu "
    '""Saudi Arabia"" app. Don\'t miss out on this Temu ""Saudi Arabia"" coupon '
    'SAR100 off and Temu ""Saudi Arabia"" coupon code SAR100 off opportunity. '
    "Here are the exclusive offers for new customers:\r\n"
    '[""ack887223""]: Flat SAR100 discount for new users\r\n'
    'How To Redeem The Temu ""Saudi Arabia"" Coupon SAR100 Off For New '
    "Customers?\r\n"
    'Redeeming your Temu ""Saudi Arabia"" SAR100 coupon is quick and easy. Follow '
    'this step-by-step guide to use the Temu ""Saudi Arabia"" SAR100 off coupon '
    "code for new users:\r\n"
    'Download the Temu ""Saudi Arabia"" app or visit their website\r\n'
    "Create a new account\r\n"
    "Browse through the wide selection of products\r\n"
    "Add your desired items to the cart\r\n"
    "Proceed to checkout\r\n"
    'Enter the coupon code [""ack887223""] in the designated field\r\n'
    "Apply the code and watch your total decrease by SAR100\r\n"
    "Complete your purchase and enjoy your savings!\r\n"
    'Temu ""Saudi Arabia"" Coupon SAR100 Off For Existing Customers\r\n'
    "Existing users can also enjoy great benefits by using our coupon code on the "
    'Temu ""Saudi Arabia"" app. Take advantage of these Temu ""Saudi Arabia"" '
    'SAR100 coupon codes for existing users and Temu ""Saudi Arabia"" coupon '
    "SAR100 off for existing customers free shipping offers:\r\n"
    '[""ack887223""]: SAR100 extra discount for existing Temu ""Saudi Arabia"" '
    "users\r\n"
    'Latest Temu ""Saudi Arabia"" Coupon SAR100 Off First Order\r\n'
    "Customers can get the highest benefits by using our coupon code during their "
    'first order. Don\'t miss out on these Temu ""Saudi Arabia"" coupon code '
    'SAR100 off first order, Temu ""Saudi Arabia"" coupon code first order, and '
    'Temu ""Saudi Arabia"" coupon code SAR100 off first time user offers:\r\n'
    '[""ack887223""]: Flat SAR100 discount for the first order\r\n'
    'How To Find The Temu ""Saudi Arabia"" Coupon Code SAR100 Off?\r\n'
    'Looking for the latest Temu ""Saudi Arabia"" coupon SAR100 off or browsing '
    'Temu ""Saudi Arabia"" coupon SAR100 off Reddit threads? We\'ve got you '
    "covered with some insider tips on finding the best deals:\r\n"
    'Sign up for the Temu ""Saudi Arabia"" newsletter to receive verified and '
    "tested coupons directly in your inbox.\r\n"
    'Follow Temu ""Saudi Arabia""\'s social media pages to stay updated on the '
    "latest coupons and promotions.\r\n"
    "Visit trusted coupon sites (like ours!) to find the most recent and working "
    'Temu ""Saudi Arabia"" coupon codes.\r\n'
    'By following these steps, you\'ll never miss out on amazing Temu ""Saudi '
    'Arabia"" discounts and offers!\r\n'
    'Is Temu ""Saudi Arabia"" SAR100 Off Coupon Legit?\r\n'
    'You might be wondering, ""Is the Temu ""Saudi Arabia"" SAR100 Off Coupon '
    'Legit?"" or ""Is the Temu ""Saudi Arabia"" 100 off coupon legit?"" We\'re '
    'here to assure you that our Temu ""Saudi Arabia"" coupon code '
    '[""ack887223""] is absolutely legitimate. Any customer can safely use our '
    'Temu ""Saudi Arabia"" coupon code to get SAR100 off on their first order and '
    "subsequent purchases.\r\n"
    "Our code is not only legit but also regularly tested and verified to ensure "
    'it works flawlessly for all our users. What\'s more, our Temu ""Saudi '
    'Arabia"" coupon code is valid worldwide and doesn\'t have an expiration '
    "date, giving you the flexibility to use it whenever you're ready to make a "
    "purchase.\r\n"
    'How Does Temu ""Saudi Arabia"" SAR100 Off Coupon Work?\r\n'
    'The Temu ""Saudi Arabia"" coupon code SAR100 off first-time user and Temu '
    '""Saudi Arabia"" coupon codes 100 off work by providing an instant discount '
    'at checkout. When you apply the coupon code [""ack887223""] during the '
    "payment process, it automatically deducts SAR100 from your total purchase "
    "amount. This discount is applied before taxes and shipping fees, maximizing "
    'your savings on Temu ""Saudi Arabia""\'s already competitive prices.\r\n'
    'These benefits make shopping on Temu ""Saudi Arabia"" even more appealing '
    "and cost-effective for savvy shoppers like you!\r\n"
    "Don't miss out on this incredible opportunity to save big with our Temu "
    '""Saudi Arabia"" coupon code SAR100 off. Whether you\'re a new or existing '
    'customer, there\'s never been a better time to shop on Temu ""Saudi Arabia"" '
    "and enjoy massive discounts.\r\n"
    'Remember to use our exclusive Temu ""Saudi Arabia"" coupon SAR100 off code '
    '[""ack887223""] to maximize your savings on your next Temu ""Saudi Arabia"" '
    "purchase. Happy shopping and enjoy your incredible deals!\r\n"
    'FAQs Of Temu ""Saudi Arabia"" SAR100 Off Coupon\r\n'
    'Q: Can I use the Temu ""Saudi Arabia"" SAR100 off coupon more than once? A: '
    'The Temu ""Saudi Arabia"" SAR100 off coupon is typically for one-time use '
    "per account. However, you may be able to use it on multiple orders if "
    "specified in the terms and conditions. Always check the current offer "
    "details for the most accurate information.\r\n"
    'Q: Does the Temu ""Saudi Arabia"" SAR100 off coupon work for international '
    'orders? A: Yes, our Temu ""Saudi Arabia"" SAR100 off coupon code '
    '[""ack887223""] is valid for orders in 68 countries worldwide, including the '
    "USA, Canada, and many European nations. Be sure to check if your country is "
    "included before placing an order.\r\n"
    'Q: Can I combine the Temu ""Saudi Arabia"" SAR100 off coupon with other '
    "promotions? A: While the SAR100 off coupon usually can't be combined with "
    "other promo codes, it can often be used in conjunction with ongoing sales or "
    'discounts on the Temu ""Saudi Arabia"" platform. This allows you to maximize '
    "your savings on your purchase.\r\n"
    'Q: Is there a minimum purchase amount required to use the Temu ""Saudi '
    'Arabia"" SAR100 off coupon? A: Our Temu ""Saudi Arabia"" coupon code '
    '[""ack887223""] for SAR100 off typically doesn\'t have a minimum purchase '
    "requirement. However, it's always best to check the current terms and "
    "conditions of the offer to be sure.\r\n"
    'Q: What should I do if the Temu ""Saudi Arabia"" SAR100 off coupon code '
    "doesn't work? A: If you're having trouble with the coupon code, first ensure "
    "you've entered it correctly. If issues persist, try clearing your browser "
    "cache or using a different device. If the problem continues, contact Temu "
    '""Saudi Arabia"" customer support for assistance '
    "https://survivetheark.com/index.php?/clubs/"
    "18284-temucoupon-discount-code-40-off%E2%9E%A4-aci789589-for-existing-customers/ "
    "https://survivetheark.com/index.php?/clubs/"
    "18329-temucoupon-discount-code-acx009224-100-off%E2%A4%A0-for-existing-user/\r\n"
    '"',
    '"New users at Temu ""UAE"" receive a AED100 discount on orders over AED100 '
    'Use the code [""ack887223""] during checkout to get Temu ""UAE"" Discount '
    "AED100 off For New Users. You n save AED100 off your first order with the "
    "coupon code available for a limited time only.\r\n"
    "Extra 30% off for new and existing customers + Up to AED100 % off & more.\r\n"
    'Temu ""UAE"" coupon codes for New users- [""ack887223""]\r\n'
    'Temu ""UAE"" discount code for New customers- [""ack887223""]\r\n'
    'Temu ""UAE"" AED100 coupon code- [""ack887223""]\r\n'
    'what are Temu ""UAE"" codes- ""ack887223""\r\n'
    'does Temu ""UAE"" give you AED100 - [""ack887223""] Yes Verified\r\n'
    'Temu ""UAE"" coupon code January 2025- {""ack887223""}\r\n'
    'Temu ""UAE"" New customer offer {""ack887223""}\r\n'
    'Temu ""UAE"" discount code 2025 {""ack887223""}\r\n'
    '100 off coupon code Temu ""UAE"" {""ack887223""}\r\n'
    'Temu ""UAE"" 100% off any order {""ack887223""}\r\n'
    '100 dollar off Temu ""UAE"" code {""ack887223""}\r\n'
    'Temu ""UAE"" coupon AED100 off for New customers\r\n'
    "There are a number of discounts and deals shoppers n take advantage of with "
    'the Teemu Coupon Bundle [""ack887223""]. Temu ""UAE"" coupon AED100 off for '
    'New customers""ack887223"" will save you AED100 on your order. To get a '
    "discount, click on the item to purchase and enter the code. You n think of "
    "it as a supercharged savings pack for all your shopping needs\r\n"
    'Temu ""UAE"" coupon code 80% off – [""ack887223""]\r\n'
    'Free Temu ""UAE"" codes 50% off – [ack887223]\r\n'
    'Temu ""UAE"" coupon AED100 off – [""ack887223""]\r\n'
    'Temu ""UAE"" buy to get BD39 – [""ack887223""]\r\n'
    'Temu ""UAE"" 129 coupon bundle – [""ack887223""]\r\n'
    'Temu ""UAE"" buy 3 to get €99 – [""ack887223""]\r\n'
    'Exclusive AED100 Off Temu ""UAE"" Discount Code\r\n'
    'Temu ""UAE"" AED100 Off Coupon Code : (""ack887223"")\r\n'
    'Temu ""UAE"" Discount Code AED100 Bundle ""ack887223"")""ack887223""\r\n'
    'Temu ""UAE"" AED100 off coupon code for Exsting users : (""ack887223"")\r\n'
    'Temu ""UAE"" coupon code AED100 off\r\n'
    'Temu ""UAE"" AED100 % OFF promo code ""ack887223"" will save you AED100 on '
    "your order. To get a discount, click on the item to purchase and enter the "
    "code.\r\n"
    'Yes, Temu ""UAE"" offers AED100 off coupon code “""ack887223""” for first '
    "time users. You n get a AED100 bonus plus 30% off any purchase at Temu "
    '""UAE"" with the AED100 Coupon Bundle at Temu ""UAE"" if you sign up with '
    'the referral code [""ack887223""] and make a first purchase of AED100 or '
    "more.\r\n"
    'Temu ""UAE"" coupon code 100 off-{""ack887223""}\r\n'
    'Temu ""UAE"" coupon code -{""ack887223""}\r\n'
    'Temu ""UAE"" coupon code AED100 off-{""ack887223""}\r\n'
    'kubonus code -{""ack887223""}\r\n'
    'Are you looking for incredible savings on your next Temu ""UAE"" purchase? '
    'Look no further! We\'ve got the ultimate Temu ""UAE"" coupon code AED100 off '
    "that will make your shopping experience even more rewarding. Our exclusive "
    'coupon code [""ack887223""] offers maximum benefits for shoppers in the USA, '
    "Canada, and European nations.\r\n"
    'Don\'t miss out on this opportunity to save big with our Temu ""UAE"" coupon '
    'AED100 off and Temu ""UAE"" 100 off coupon code. Whether you\'re a new '
    'customer or a loyal Temu ""UAE"" shopper, we\'ve got you covered with '
    "amazing discounts and perks.\r\n"
    'What Is The Coupon Code For Temu ""UAE"" AED100 Off?\r\n'
    "Both new and existing customers can enjoy fantastic benefits by using our "
    'AED100 coupon code on the Temu ""UAE"" app and website. Take advantage of '
    'this Temu ""UAE"" coupon AED100 off and AED100 off Temu ""UAE"" coupon to '
    "maximize your savings. Here are some of the incredible offers you can unlock "
    'with our coupon code [""ack887223""]:\r\n'
    '[""ack887223""]: Flat AED100 off on your purchase\r\n'
    'Temu ""UAE"" Coupon Code AED100 Off For New Users In 2025\r\n'
    "New users can reap the highest benefits by using our coupon code on the Temu "
    '""UAE"" app. Don\'t miss out on this Temu ""UAE"" coupon AED100 off and Temu '
    '""UAE"" coupon code AED100 off opportunity. Here are the exclusive offers '
    "for new customers:\r\n"
    '[""ack887223""]: Flat AED100 discount for new users\r\n'
    'How To Redeem The Temu ""UAE"" Coupon AED100 Off For New Customers?\r\n'
    'Redeeming your Temu ""UAE"" AED100 coupon is quick and easy. Follow this '
    'step-by-step guide to use the Temu ""UAE"" AED100 off coupon code for new '
    "users:\r\n"
    'Download the Temu ""UAE"" app or visit their website\r\n'
    "Create a new account\r\n"
    "Browse through the wide selection of products\r\n"
    "Add your desired items to the cart\r\n"
    "Proceed to checkout\r\n"
    'Enter the coupon code [""ack887223""] in the designated field\r\n'
    "Apply the code and watch your total decrease by AED100\r\n"
    "Complete your purchase and enjoy your savings!\r\n"
    'Temu ""UAE"" Coupon AED100 Off For Existing Customers\r\n'
    "Existing users can also enjoy great benefits by using our coupon code on the "
    'Temu ""UAE"" app. Take advantage of these Temu ""UAE"" AED100 coupon codes '
    'for existing users and Temu ""UAE"" coupon AED100 off for existing customers '
    "free shipping offers:\r\n"
    '[""ack887223""]: AED100 extra discount for existing Temu ""UAE"" users\r\n'
    'Latest Temu ""UAE"" Coupon AED100 Off First Order\r\n'
    "Customers can get the highest benefits by using our coupon code during their "
    'first order. Don\'t miss out on these Temu ""UAE"" coupon code AED100 off '
    'first order, Temu ""UAE"" coupon code first order, and Temu ""UAE"" coupon '
    "code AED100 off first time user offers:\r\n"
    '[""ack887223""]: Flat AED100 discount for the first order\r\n'
    'How To Find The Temu ""UAE"" Coupon Code AED100 Off?\r\n'
    'Looking for the latest Temu ""UAE"" coupon AED100 off or browsing Temu '
    '""UAE"" coupon AED100 off Reddit threads? We\'ve got you covered with some '
    "insider tips on finding the best deals:\r\n"
    'Sign up for the Temu ""UAE"" newsletter to receive verified and tested '
    "coupons directly in your inbox.\r\n"
    'Follow Temu ""UAE""\'s social media pages to stay updated on the latest '
    "coupons and promotions.\r\n"
    "Visit trusted coupon sites (like ours!) to find the most recent and working "
    'Temu ""UAE"" coupon codes.\r\n'
    'By following these steps, you\'ll never miss out on amazing Temu ""UAE"" '
    "discounts and offers!\r\n"
    'Is Temu ""UAE"" AED100 Off Coupon Legit?\r\n'
    'You might be wondering, ""Is the Temu ""UAE"" AED100 Off Coupon Legit?"" or '
    '""Is the Temu ""UAE"" 100 off coupon legit?"" We\'re here to assure you that '
    'our Temu ""UAE"" coupon code [""ack887223""] is absolutely legitimate. Any '
    'customer can safely use our Temu ""UAE"" coupon code to get AED100 off on '
    "their first order and subsequent purchases.\r\n"
    "Our code is not only legit but also regularly tested and verified to ensure "
    'it works flawlessly for all our users. What\'s more, our Temu ""UAE"" coupon '
    "code is valid worldwide and doesn't have an expiration date, giving you the "
    "flexibility to use it whenever you're ready to make a purchase.\r\n"
    'How Does Temu ""UAE"" AED100 Off Coupon Work?\r\n'
    'The Temu ""UAE"" coupon code AED100 off first-time user and Temu ""UAE"" '
    "coupon codes 100 off work by providing an instant discount at checkout. When "
    'you apply the coupon code [""ack887223""] during the payment process, it '
    "automatically deducts AED100 from your total purchase amount. This discount "
    "is applied before taxes and shipping fees, maximizing your savings on Temu "
    '""UAE""\'s already competitive prices.\r\n'
    'These benefits make shopping on Temu ""UAE"" even more appealing and '
    "cost-effective for savvy shoppers like you!\r\n"
    "Don't miss out on this incredible opportunity to save big with our Temu "
    '""UAE"" coupon code AED100 off. Whether you\'re a new or existing customer, '
    'there\'s never been a better time to shop on Temu ""UAE"" and enjoy massive '
    "discounts.\r\n"
    'Remember to use our exclusive Temu ""UAE"" coupon AED100 off code '
    '[""ack887223""] to maximize your savings on your next Temu ""UAE"" purchase. '
    "Happy shopping and enjoy your incredible deals!\r\n"
    'FAQs Of Temu ""UAE"" AED100 Off Coupon\r\n'
    'Q: Can I use the Temu ""UAE"" AED100 off coupon more than once? A: The Temu '
    '""UAE"" AED100 off coupon is typically for one-time use per account. '
    "However, you may be able to use it on multiple orders if specified in the "
    "terms and conditions. Always check the current offer details for the most "
    "accurate information.\r\n"
    'Q: Does the Temu ""UAE"" AED100 off coupon work for international orders? A: '
    'Yes, our Temu ""UAE"" AED100 off coupon code [""ack887223""] is valid for '
    "orders in 68 countries worldwide, including the USA, Canada, and many "
    "European nations. Be sure to check if your country is included before "
    "placing an order.\r\n"
    'Q: Can I combine the Temu ""UAE"" AED100 off coupon with other promotions? '
    "A: While the AED100 off coupon usually can't be combined with other promo "
    "codes, it can often be used in conjunction with ongoing sales or discounts "
    'on the Temu ""UAE"" platform. This allows you to maximize your savings on '
    "your purchase.\r\n"
    'Q: Is there a minimum purchase amount required to use the Temu ""UAE"" '
    'AED100 off coupon? A: Our Temu ""UAE"" coupon code [""ack887223""] for '
    "AED100 off typically doesn't have a minimum purchase requirement. However, "
    "it's always best to check the current terms and conditions of the offer to "
    "be sure.\r\n"
    'Q: What should I do if the Temu ""UAE"" AED100 off coupon code doesn\'t '
    "work? A: If you're having trouble with the coupon code, first ensure you've "
    "entered it correctly. If issues persist, try clearing your browser cache or "
    'using a different device. If the problem continues, contact Temu ""UAE"" '
    "customer support for assistance "
    "https://survivetheark.com/index.php?/clubs/"
    "18284-temucoupon-discount-code-40-off%E2%9E%A4-aci789589-for-existing-customers/ "
    "https://survivetheark.com/index.php?/clubs/"
    "18329-temucoupon-discount-code-acx009224-100-off%E2%A4%A0-for-existing-user/\r\n"
    '"',
    '"New users at Temu ""Pakistan"" receive a PKR100 discount on orders over '
    'PKR100 Use the code [""ack887223""] during checkout to get Temu ""Pakistan"" '
    "Discount PKR100 off For New Users. You n save PKR100 off your first order "
    "with the coupon code available for a limited time only.\r\n"
    "Extra 30% off for new and existing customers + Up to PKR100 % off & more.\r\n"
    'Temu ""Pakistan"" coupon codes for New users- [""ack887223""]\r\n'
    'Temu ""Pakistan"" discount code for New customers- [""ack887223""]\r\n'
    'Temu ""Pakistan"" PKR100 coupon code- [""ack887223""]\r\n'
    'what are Temu ""Pakistan"" codes- ""ack887223""\r\n'
    'does Temu ""Pakistan"" give you PKR100 - [""ack887223""] Yes Verified\r\n'
    'Temu ""Pakistan"" coupon code January 2025- {""ack887223""}\r\n'
    'Temu ""Pakistan"" New customer offer {""ack887223""}\r\n'
    'Temu ""Pakistan"" discount code 2025 {""ack887223""}\r\n'
    '100 off coupon code Temu ""Pakistan"" {""ack887223""}\r\n'
    'Temu ""Pakistan"" 100% off any order {""ack887223""}\r\n'
    '100 dollar off Temu ""Pakistan"" code {""ack887223""}\r\n'
    'Temu ""Pakistan"" coupon PKR100 off for New customers\r\n'
    "There are a number of discounts and deals shoppers n take advantage of with "
    'the Teemu Coupon Bundle [""ack887223""]. Temu ""Pakistan"" coupon PKR100 off '
    'for New customers""ack887223"" will save you PKR100 on your order. To get a '
    "discount, click on the item to purchase and enter the code. You n think of "
    "it as a supercharged savings pack for all your shopping needs\r\n"
    'Temu ""Pakistan"" coupon code 80% off – [""ack887223""]\r\n'
    'Free Temu ""Pakistan"" codes 50% off – [ack887223]\r\n'
    'Temu ""Pakistan"" coupon PKR100 off – [""ack887223""]\r\n'
    'Temu ""Pakistan"" buy to get BD39 – [""ack887223""]\r\n'
    'Temu ""Pakistan"" 129 coupon bundle – [""ack887223""]\r\n'
    'Temu ""Pakistan"" buy 3 to get €99 – [""ack887223""]\r\n'
    'Exclusive PKR100 Off Temu ""Pakistan"" Discount Code\r\n'
    'Temu ""Pakistan"" PKR100 Off Coupon Code : (""ack887223"")\r\n'
    'Temu ""Pakistan"" Discount Code PKR100 Bundle ""ack887223"")""ack887223""\r\n'
    'Temu ""Pakistan"" PKR100 off coupon code for Exsting users : '
    '(""ack887223"")\r\n'
    'Temu ""Pakistan"" coupon code PKR100 off\r\n'
    'Temu ""Pakistan"" PKR100 % OFF promo code ""ack887223"" will save you PKR100 '
    "on your order. To get a discount, click on the item to purchase and enter "
    "the code.\r\n"
    'Yes, Temu ""Pakistan"" offers PKR100 off coupon code “""ack887223""” for '
    "first time users. You n get a PKR100 bonus plus 30% off any purchase at Temu "
    '""Pakistan"" with the PKR100 Coupon Bundle at Temu ""Pakistan"" if you sign '
    'up with the referral code [""ack887223""] and make a first purchase of '
    "PKR100 or more.\r\n"
    'Temu ""Pakistan"" coupon code 100 off-{""ack887223""}\r\n'
    'Temu ""Pakistan"" coupon code -{""ack887223""}\r\n'
    'Temu ""Pakistan"" coupon code PKR100 off-{""ack887223""}\r\n'
    'kubonus code -{""ack887223""}\r\n'
    'Are you looking for incredible savings on your next Temu ""Pakistan"" '
    'purchase? Look no further! We\'ve got the ultimate Temu ""Pakistan"" coupon '
    "code PKR100 off that will make your shopping experience even more rewarding. "
    'Our exclusive coupon code [""ack887223""] offers maximum benefits for '
    "shoppers in the USA, Canada, and European nations.\r\n"
    'Don\'t miss out on this opportunity to save big with our Temu ""Pakistan"" '
    'coupon PKR100 off and Temu ""Pakistan"" 100 off coupon code. Whether you\'re '
    'a new customer or a loyal Temu ""Pakistan"" shopper, we\'ve got you covered '
    "with amazing discounts and perks.\r\n"
    'What Is The Coupon Code For Temu ""Pakistan"" PKR100 Off?\r\n'
    "Both new and existing customers can enjoy fantastic benefits by using our "
    'PKR100 coupon code on the Temu ""Pakistan"" app and website. Take advantage '
    'of this Temu ""Pakistan"" coupon PKR100 off and PKR100 off Temu ""Pakistan"" '
    "coupon to maximize your savings. Here are some of the incredible offers you "
    'can unlock with our coupon code [""ack887223""]:\r\n'
    '[""ack887223""]: Flat PKR100 off on your purchase\r\n'
    'Temu ""Pakistan"" Coupon Code PKR100 Off For New Users In 2025\r\n'
    "New users can reap the highest benefits by using our coupon code on the Temu "
    '""Pakistan"" app. Don\'t miss out on this Temu ""Pakistan"" coupon PKR100 '
    'off and Temu ""Pakistan"" coupon code PKR100 off opportunity. Here are the '
    "exclusive offers for new customers:\r\n"
    '[""ack887223""]: Flat PKR100 discount for new users\r\n'
    'How To Redeem The Temu ""Pakistan"" Coupon PKR100 Off For New Customers?\r\n'
    'Redeeming your Temu ""Pakistan"" PKR100 coupon is quick and easy. Follow '
    'this step-by-step guide to use the Temu ""Pakistan"" PKR100 off coupon code '
    "for new users:\r\n"
    'Download the Temu ""Pakistan"" app or visit their website\r\n'
    "Create a new account\r\n"
    "Browse through the wide selection of products\r\n"
    "Add your desired items to the cart\r\n"
    "Proceed to checkout\r\n"
    'Enter the coupon code [""ack887223""] in the designated field\r\n'
    "Apply the code and watch your total decrease by PKR100\r\n"
    "Complete your purchase and enjoy your savings!\r\n"
    'Temu ""Pakistan"" Coupon PKR100 Off For Existing Customers\r\n'
    "Existing users can also enjoy great benefits by using our coupon code on the "
    'Temu ""Pakistan"" app. Take advantage of these Temu ""Pakistan"" PKR100 '
    'coupon codes for existing users and Temu ""Pakistan"" coupon PKR100 off for '
    "existing customers free shipping offers:\r\n"
    '[""ack887223""]: PKR100 extra discount for existing Temu ""Pakistan"" '
    "users\r\n"
    'Latest Temu ""Pakistan"" Coupon PKR100 Off First Order\r\n'
    "Customers can get the highest benefits by using our coupon code during their "
    'first order. Don\'t miss out on these Temu ""Pakistan"" coupon code PKR100 '
    'off first order, Temu ""Pakistan"" coupon code first order, and Temu '
    '""Pakistan"" coupon code PKR100 off first time user offers:\r\n'
    '[""ack887223""]: Flat PKR100 discount for the first order\r\n'
    'How To Find The Temu ""Pakistan"" Coupon Code PKR100 Off?\r\n'
    'Looking for the latest Temu ""Pakistan"" coupon PKR100 off or browsing Temu '
    '""Pakistan"" coupon PKR100 off Reddit threads? We\'ve got you covered with '
    "some insider tips on finding the best deals:\r\n"
    'Sign up for the Temu ""Pakistan"" newsletter to receive verified and tested '
    "coupons directly in your inbox.\r\n"
    'Follow Temu ""Pakistan""\'s social media pages to stay updated on the latest '
    "coupons and promotions.\r\n"
    "Visit trusted coupon sites (like ours!) to find the most recent and working "
    'Temu ""Pakistan"" coupon codes.\r\n'
    "By following these steps, you'll never miss out on amazing Temu "
    '""Pakistan"" discounts and offers!\r\n'
    'Is Temu ""Pakistan"" PKR100 Off Coupon Legit?\r\n'
    'You might be wondering, ""Is the Temu ""Pakistan"" PKR100 Off Coupon '
    'Legit?"" or ""Is the Temu ""Pakistan"" 100 off coupon legit?"" We\'re here '
    'to assure you that our Temu ""Pakistan"" coupon code [""ack887223""] is '
    'absolutely legitimate. Any customer can safely use our Temu ""Pakistan"" '
    "coupon code to get PKR100 off on their first order and subsequent "
    "purchases.\r\n"
    "Our code is not only legit but also regularly tested and verified to ensure "
    'it works flawlessly for all our users. What\'s more, our Temu ""Pakistan"" '
    "coupon code is valid worldwide and doesn't have an expiration date, giving "
    "you the flexibility to use it whenever you're ready to make a purchase.\r\n"
    'How Does Temu ""Pakistan"" PKR100 Off Coupon Work?\r\n'
    'The Temu ""Pakistan"" coupon code PKR100 off first-time user and Temu '
    '""Pakistan"" coupon codes 100 off work by providing an instant discount at '
    'checkout. When you apply the coupon code [""ack887223""] during the payment '
    "process, it automatically deducts PKR100 from your total purchase amount. "
    "This discount is applied before taxes and shipping fees, maximizing your "
    'savings on Temu ""Pakistan""\'s already competitive prices.\r\n'
    'These benefits make shopping on Temu ""Pakistan"" even more appealing and '
    "cost-effective for savvy shoppers like you!\r\n"
    "Don't miss out on this incredible opportunity to save big with our Temu "
    '""Pakistan"" coupon code PKR100 off. Whether you\'re a new or existing '
    'customer, there\'s never been a better time to shop on Temu ""Pakistan"" and '
    "enjoy massive discounts.\r\n"
    'Remember to use our exclusive Temu ""Pakistan"" coupon PKR100 off code '
    '[""ack887223""] to maximize your savings on your next Temu ""Pakistan"" '
    "purchase. Happy shopping and enjoy your incredible deals!\r\n"
    'FAQs Of Temu ""Pakistan"" PKR100 Off Coupon\r\n'
    'Q: Can I use the Temu ""Pakistan"" PKR100 off coupon more than once? A: The '
    'Temu ""Pakistan"" PKR100 off coupon is typically for one-time use per '
    "account. However, you may be able to use it on multiple orders if specified "
    "in the terms and conditions. Always check the current offer details for the "
    "most accurate information.\r\n"
    'Q: Does the Temu ""Pakistan"" PKR100 off coupon work for international '
    'orders? A: Yes, our Temu ""Pakistan"" PKR100 off coupon code [""ack887223""] '
    "is valid for orders in 68 countries worldwide, including the USA, Canada, "
    "and many European nations. Be sure to check if your country is included "
    "before placing an order.\r\n"
    'Q: Can I combine the Temu ""Pakistan"" PKR100 off coupon with other '
    "promotions? A: While the PKR100 off coupon usually can't be combined with "
    "other promo codes, it can often be used in conjunction with ongoing sales or "
    'discounts on the Temu ""Pakistan"" platform. This allows you to maximize '
    "your savings on your purchase.\r\n"
    'Q: Is there a minimum purchase amount required to use the Temu ""Pakistan"" '
    'PKR100 off coupon? A: Our Temu ""Pakistan"" coupon code [""ack887223""] for '
    "PKR100 off typically doesn't have a minimum purchase requirement. However, "
    "it's always best to check the current terms and conditions of the offer to "
    "be sure.\r\n"
    'Q: What should I do if the Temu ""Pakistan"" PKR100 off coupon code doesn\'t '
    "work? A: If you're having trouble with the coupon code, first ensure you've "
    "entered it correctly. If issues persist, try clearing your browser cache or "
    "using a different device. If the problem continues, contact Temu "
    '""Pakistan"" customer support for assistance '
    "https://survivetheark.com/index.php?/clubs/"
    "18284-temucoupon-discount-code-40-off%E2%9E%A4-aci789589-for-existing-customers/ "
    "https://survivetheark.com/index.php?/clubs/"
    "18329-temucoupon-discount-code-acx009224-100-off%E2%A4%A0-for-existing-user/\r\n"
    '"',
    '"New users at Temu ""Bahrain"" receive a BD100 discount on orders over BD100 '
    'Use the code [""ack887223""] during checkout to get Temu ""Bahrain"" '
    "Discount BD100 off For New Users. You n save BD100 off your first order with "
    "the coupon code available for a limited time only.\r\n"
    "Extra 30% off for new and existing customers + Up to BD100 % off & more.\r\n"
    'Temu ""Bahrain"" coupon codes for New users- [""ack887223""]\r\n'
    'Temu ""Bahrain"" discount code for New customers- [""ack887223""]\r\n'
    'Temu ""Bahrain"" BD100 coupon code- [""ack887223""]\r\n'
    'what are Temu ""Bahrain"" codes- ""ack887223""\r\n'
    'does Temu ""Bahrain"" give you BD100 - [""ack887223""] Yes Verified\r\n'
    'Temu ""Bahrain"" coupon code January 2025- {""ack887223""}\r\n'
    'Temu ""Bahrain"" New customer offer {""ack887223""}\r\n'
    'Temu ""Bahrain"" discount code 2025 {""ack887223""}\r\n'
    '100 off coupon code Temu ""Bahrain"" {""ack887223""}\r\n'
    'Temu ""Bahrain"" 100% off any order {""ack887223""}\r\n'
    '100 dollar off Temu ""Bahrain"" code {""ack887223""}\r\n'
    'Temu ""Bahrain"" coupon BD100 off for New customers\r\n'
    "There are a number of discounts and deals shoppers n take advantage of with "
    'the Teemu Coupon Bundle [""ack887223""]. Temu ""Bahrain"" coupon BD100 off '
    'for New customers""ack887223"" will save you BD100 on your order. To get a '
    "discount, click on the item to purchase and enter the code. You n think of "
    "it as a supercharged savings pack for all your shopping needs\r\n"
    'Temu ""Bahrain"" coupon code 80% off – [""ack887223""]\r\n'
    'Free Temu ""Bahrain"" codes 50% off – [ack887223]\r\n'
    'Temu ""Bahrain"" coupon BD100 off – [""ack887223""]\r\n'
    'Temu ""Bahrain"" buy to get BD39 – [""ack887223""]\r\n'
    'Temu ""Bahrain"" 129 coupon bundle – [""ack887223""]\r\n'
    'Temu ""Bahrain"" buy 3 to get €99 – [""ack887223""]\r\n'
    'Exclusive BD100 Off Temu ""Bahrain"" Discount Code\r\n'
    'Temu ""Bahrain"" BD100 Off Coupon Code : (""ack887223"")\r\n'
    'Temu ""Bahrain"" Discount Code BD100 Bundle ""ack887223"")""ack887223""\r\n'
    'Temu ""Bahrain"" BD100 off coupon code for Exsting users : '
    '(""ack887223"")\r\n'
    'Temu ""Bahrain"" coupon code BD100 off\r\n'
    'Temu ""Bahrain"" BD100 % OFF promo code ""ack887223"" will save you BD100 on '
    "your order. To get a discount, click on the item to purchase and enter the "
    "code.\r\n"
    'Yes, Temu ""Bahrain"" offers BD100 off coupon code “""ack887223""” for first '
    "time users. You n get a BD100 bonus plus 30% off any purchase at Temu "
    '""Bahrain"" with the BD100 Coupon Bundle at Temu ""Bahrain"" if you sign up '
    'with the referral code [""ack887223""] and make a first purchase of BD100 or '
    "more.\r\n"
    'Temu ""Bahrain"" coupon code 100 off-{""ack887223""}\r\n'
    'Temu ""Bahrain"" coupon code -{""ack887223""}\r\n'
    'Temu ""Bahrain"" coupon code BD100 off-{""ack887223""}\r\n'
    'kubonus code -{""ack887223""}\r\n'
    'Are you looking for incredible savings on your next Temu ""Bahrain"" '
    'purchase? Look no further! We\'ve got the ultimate Temu ""Bahrain"" coupon '
    "code BD100 off that will make your shopping experience even more rewarding. "
    'Our exclusive coupon code [""ack887223""] offers maximum benefits for '
    "shoppers in the USA, Canada, and European nations.\r\n"
    'Don\'t miss out on this opportunity to save big with our Temu ""Bahrain"" '
    'coupon BD100 off and Temu ""Bahrain"" 100 off coupon code. Whether you\'re a '
    'new customer or a loyal Temu ""Bahrain"" shopper, we\'ve got you covered '
    "with amazing discounts and perks.\r\n"
    'What Is The Coupon Code For Temu ""Bahrain"" BD100 Off?\r\n'
    "Both new and existing customers can enjoy fantastic benefits by using our "
    'BD100 coupon code on the Temu ""Bahrain"" app and website. Take advantage of '
    'this Temu ""Bahrain"" coupon BD100 off and BD100 off Temu ""Bahrain"" coupon '
    "to maximize your savings. Here are some of the incredible offers you can "
    'unlock with our coupon code [""ack887223""]:\r\n'
    '[""ack887223""]: Flat BD100 off on your purchase\r\n'
    'Temu ""Bahrain"" Coupon Code BD100 Off For New Users In 2025\r\n'
    "New users can reap the highest benefits by using our coupon code on the Temu "
    '""Bahrain"" app. Don\'t miss out on this Temu ""Bahrain"" coupon BD100 off '
    'and Temu ""Bahrain"" coupon code BD100 off opportunity. Here are the '
    "exclusive offers for new customers:\r\n"
    '[""ack887223""]: Flat BD100 discount for new users\r\n'
    'How To Redeem The Temu ""Bahrain"" Coupon BD100 Off For New Customers?\r\n'
    'Redeeming your Temu ""Bahrain"" BD100 coupon is quick and easy. Follow this '
    'step-by-step guide to use the Temu ""Bahrain"" BD100 off coupon code for new '
    "users:\r\n"
    'Download the Temu ""Bahrain"" app or visit their website\r\n'
    "Create a new account\r\n"
    "Browse through the wide selection of products\r\n"
    "Add your desired items to the cart\r\n"
    "Proceed to checkout\r\n"
    'Enter the coupon code [""ack887223""] in the designated field\r\n'
    "Apply the code and watch your total decrease by BD100\r\n"
    "Complete your purchase and enjoy your savings!\r\n"
    'Temu ""Bahrain"" Coupon BD100 Off For Existing Customers\r\n'
    "Existing users can also enjoy great benefits by using our coupon code on the "
    'Temu ""Bahrain"" app. Take advantage of these Temu ""Bahrain"" BD100 coupon '
    'codes for existing users and Temu ""Bahrain"" coupon BD100 off for existing '
    "customers free shipping offers:\r\n"
    '[""ack887223""]: BD100 extra discount for existing Temu ""Bahrain"" users\r\n'
    'Latest Temu ""Bahrain"" Coupon BD100 Off First Order\r\n'
    "Customers can get the highest benefits by using our coupon code during their "
    'first order. Don\'t miss out on these Temu ""Bahrain"" coupon code BD100 off '
    'first order, Temu ""Bahrain"" coupon code first order, and Temu ""Bahrain"" '
    "coupon code BD100 off first time user offers:\r\n"
    '[""ack887223""]: Flat BD100 discount for the first order\r\n'
    'How To Find The Temu ""Bahrain"" Coupon Code BD100 Off?\r\n'
    'Looking for the latest Temu ""Bahrain"" coupon BD100 off or browsing Temu '
    '""Bahrain"" coupon BD100 off Reddit threads? We\'ve got you covered with '
    "some insider tips on finding the best deals:\r\n"
    'Sign up for the Temu ""Bahrain"" newsletter to receive verified and tested '
    "coupons directly in your inbox.\r\n"
    'Follow Temu ""Bahrain""\'s social media pages to stay updated on the latest '
    "coupons and promotions.\r\n"
    "Visit trusted coupon sites (like ours!) to find the most recent and working "
    'Temu ""Bahrain"" coupon codes.\r\n'
    'By following these steps, you\'ll never miss out on amazing Temu ""Bahrain"" '
    "discounts and offers!\r\n"
    'Is Temu ""Bahrain"" BD100 Off Coupon Legit?\r\n'
    'You might be wondering, ""Is the Temu ""Bahrain"" BD100 Off Coupon Legit?"" '
    'or ""Is the Temu ""Bahrain"" 100 off coupon legit?"" We\'re here to assure '
    'you that our Temu ""Bahrain"" coupon code [""ack887223""] is absolutely '
    'legitimate. Any customer can safely use our Temu ""Bahrain"" coupon code to '
    "get BD100 off on their first order and subsequent purchases.\r\n"
    "Our code is not only legit but also regularly tested and verified to ensure "
    'it works flawlessly for all our users. What\'s more, our Temu ""Bahrain"" '
    "coupon code is valid worldwide and doesn't have an expiration date, giving "
    "you the flexibility to use it whenever you're ready to make a purchase.\r\n"
    'How Does Temu ""Bahrain"" BD100 Off Coupon Work?\r\n'
    'The Temu ""Bahrain"" coupon code BD100 off first-time user and Temu '
    '""Bahrain"" coupon codes 100 off work by providing an instant discount at '
    'checkout. When you apply the coupon code [""ack887223""] during the payment '
    "process, it automatically deducts BD100 from your total purchase amount. "
    "This discount is applied before taxes and shipping fees, maximizing your "
    'savings on Temu ""Bahrain""\'s already competitive prices.\r\n'
    'These benefits make shopping on Temu ""Bahrain"" even more appealing and '
    "cost-effective for savvy shoppers like you!\r\n"
    "Don't miss out on this incredible opportunity to save big with our Temu "
    '""Bahrain"" coupon code BD100 off. Whether you\'re a new or existing '
    'customer, there\'s never been a better time to shop on Temu ""Bahrain"" and '
    "enjoy massive discounts.\r\n"
    'Remember to use our exclusive Temu ""Bahrain"" coupon BD100 off code '
    '[""ack887223""] to maximize your savings on your next Temu ""Bahrain"" '
    "purchase. Happy shopping and enjoy your incredible deals!\r\n"
    'FAQs Of Temu ""Bahrain"" BD100 Off Coupon\r\n'
    'Q: Can I use the Temu ""Bahrain"" BD100 off coupon more than once? A: The '
    'Temu ""Bahrain"" BD100 off coupon is typically for one-time use per account. '
    "However, you may be able to use it on multiple orders if specified in the "
    "terms and conditions. Always check the current offer details for the most "
    "accurate information.\r\n"
    'Q: Does the Temu ""Bahrain"" BD100 off coupon work for international orders? '
    'A: Yes, our Temu ""Bahrain"" BD100 off coupon code [""ack887223""] is valid '
    "for orders in 68 countries worldwide, including the USA, Canada, and many "
    "European nations. Be sure to check if your country is included before "
    "placing an order.\r\n"
    'Q: Can I combine the Temu ""Bahrain"" BD100 off coupon with other '
    "promotions? A: While the BD100 off coupon usually can't be combined with "
    "other promo codes, it can often be used in conjunction with ongoing sales or "
    'discounts on the Temu ""Bahrain"" platform. This allows you to maximize your '
    "savings on your purchase.\r\n"
    'Q: Is there a minimum purchase amount required to use the Temu ""Bahrain"" '
    'BD100 off coupon? A: Our Temu ""Bahrain"" coupon code [""ack887223""] for '
    "BD100 off typically doesn't have a minimum purchase requirement. However, "
    "it's always best to check the current terms and conditions of the offer to "
    "be sure.\r\n"
    'Q: What should I do if the Temu ""Bahrain"" BD100 off coupon code doesn\'t '
    "work? A: If you're having trouble with the coupon code, first ensure you've "
    "entered it correctly. If issues persist, try clearing your browser cache or "
    'using a different device. If the problem continues, contact Temu ""Bahrain"" '
    "customer support for assistance "
    "https://survivetheark.com/index.php?/clubs/"
    "18284-temucoupon-discount-code-40-off%E2%9E%A4-aci789589-for-existing-customers/ "
    "https://survivetheark.com/index.php?/clubs/"
    "18329-temucoupon-discount-code-acx009224-100-off%E2%A4%A0-for-existing-user/\r\n"
    '"',
    '"New users at Temu ""Oman"" receive a OMR100 discount on orders over OMR100 '
    'Use the code [""ack887223""] during checkout to get Temu ""Oman"" Discount '
    "OMR100 off For New Users. You n save OMR100 off your first order with the "
    "coupon code available for a limited time only.\r\n"
    "Extra 30% off for new and existing customers + Up to OMR100 % off & more.\r\n"
    'Temu ""Oman"" coupon codes for New users- [""ack887223""]\r\n'
    'Temu ""Oman"" discount code for New customers- [""ack887223""]\r\n'
    'Temu ""Oman"" OMR100 coupon code- [""ack887223""]\r\n'
    'what are Temu ""Oman"" codes- ""ack887223""\r\n'
    'does Temu ""Oman"" give you OMR100 - [""ack887223""] Yes Verified\r\n'
    'Temu ""Oman"" coupon code January 2025- {""ack887223""}\r\n'
    'Temu ""Oman"" New customer offer {""ack887223""}\r\n'
    'Temu ""Oman"" discount code 2025 {""ack887223""}\r\n'
    '100 off coupon code Temu ""Oman"" {""ack887223""}\r\n'
    'Temu ""Oman"" 100% off any order {""ack887223""}\r\n'
    '100 dollar off Temu ""Oman"" code {""ack887223""}\r\n'
    'Temu ""Oman"" coupon OMR100 off for New customers\r\n'
    "There are a number of discounts and deals shoppers n take advantage of with "
    'the Teemu Coupon Bundle [""ack887223""]. Temu ""Oman"" coupon OMR100 off for '
    'New customers""ack887223"" will save you OMR100 on your order. To get a '
    "discount, click on the item to purchase and enter the code. You n think of "
    "it as a supercharged savings pack for all your shopping needs\r\n"
    'Temu ""Oman"" coupon code 80% off – [""ack887223""]\r\n'
    'Free Temu ""Oman"" codes 50% off – [ack887223]\r\n'
    'Temu ""Oman"" coupon OMR100 off – [""ack887223""]\r\n'
    'Temu ""Oman"" buy to get BD39 – [""ack887223""]\r\n'
    'Temu ""Oman"" 129 coupon bundle – [""ack887223""]\r\n'
    'Temu ""Oman"" buy 3 to get €99 – [""ack887223""]\r\n'
    'Exclusive OMR100 Off Temu ""Oman"" Discount Code\r\n'
    'Temu ""Oman"" OMR100 Off Coupon Code : (""ack887223"")\r\n'
    'Temu ""Oman"" Discount Code OMR100 Bundle ""ack887223"")""ack887223""\r\n'
    'Temu ""Oman"" OMR100 off coupon code for Exsting users : (""ack887223"")\r\n'
    'Temu ""Oman"" coupon code OMR100 off\r\n'
    'Temu ""Oman"" OMR100 % OFF promo code ""ack887223"" will save you OMR100 on '
    "your order. To get a discount, click on the item to purchase and enter the "
    "code.\r\n"
    'Yes, Temu ""Oman"" offers OMR100 off coupon code “""ack887223""” for first '
    "time users. You n get a OMR100 bonus plus 30% off any purchase at Temu "
    '""Oman"" with the OMR100 Coupon Bundle at Temu ""Oman"" if you sign up with '
    'the referral code [""ack887223""] and make a first purchase of OMR100 or '
    "more.\r\n"
    'Temu ""Oman"" coupon code 100 off-{""ack887223""}\r\n'
    'Temu ""Oman"" coupon code -{""ack887223""}\r\n'
    'Temu ""Oman"" coupon code OMR100 off-{""ack887223""}\r\n'
    'kubonus code -{""ack887223""}\r\n'
    'Are you looking for incredible savings on your next Temu ""Oman"" purchase? '
    'Look no further! We\'ve got the ultimate Temu ""Oman"" coupon code OMR100 '
    "off that will make your shopping experience even more rewarding. Our "
    'exclusive coupon code [""ack887223""] offers maximum benefits for shoppers '
    "in the USA, Canada, and European nations.\r\n"
    'Don\'t miss out on this opportunity to save big with our Temu ""Oman"" '
    'coupon OMR100 off and Temu ""Oman"" 100 off coupon code. Whether you\'re a '
    'new customer or a loyal Temu ""Oman"" shopper, we\'ve got you covered with '
    "amazing discounts and perks.\r\n"
    'What Is The Coupon Code For Temu ""Oman"" OMR100 Off?\r\n'
    "Both new and existing customers can enjoy fantastic benefits by using our "
    'OMR100 coupon code on the Temu ""Oman"" app and website. Take advantage of '
    'this Temu ""Oman"" coupon OMR100 off and OMR100 off Temu ""Oman"" coupon to '
    "maximize your savings. Here are some of the incredible offers you can unlock "
    'with our coupon code [""ack887223""]:\r\n'
    '[""ack887223""]: Flat OMR100 off on your purchase\r\n'
    'Temu ""Oman"" Coupon Code OMR100 Off For New Users In 2025\r\n'
    "New users can reap the highest benefits by using our coupon code on the Temu "
    '""Oman"" app. Don\'t miss out on this Temu ""Oman"" coupon OMR100 off and '
    'Temu ""Oman"" coupon code OMR100 off opportunity. Here are the exclusive '
    "offers for new customers:\r\n"
    '[""ack887223""]: Flat OMR100 discount for new users\r\n'
    'How To Redeem The Temu ""Oman"" Coupon OMR100 Off For New Customers?\r\n'
    'Redeeming your Temu ""Oman"" OMR100 coupon is quick and easy. Follow this '
    'step-by-step guide to use the Temu ""Oman"" OMR100 off coupon code for new '
    "users:\r\n"
    'Download the Temu ""Oman"" app or visit their website\r\n'
    "Create a new account\r\n"
    "Browse through the wide selection of products\r\n"
    "Add your desired items to the cart\r\n"
    "Proceed to checkout\r\n"
    'Enter the coupon code [""ack887223""] in the designated field\r\n'
    "Apply the code and watch your total decrease by OMR100\r\n"
    "Complete your purchase and enjoy your savings!\r\n"
    'Temu ""Oman"" Coupon OMR100 Off For Existing Customers\r\n'
    "Existing users can also enjoy great benefits by using our coupon code on the "
    'Temu ""Oman"" app. Take advantage of these Temu ""Oman"" OMR100 coupon codes '
    'for existing users and Temu ""Oman"" coupon OMR100 off for existing '
    "customers free shipping offers:\r\n"
    '[""ack887223""]: OMR100 extra discount for existing Temu ""Oman"" users\r\n'
    'Latest Temu ""Oman"" Coupon OMR100 Off First Order\r\n'
    "Customers can get the highest benefits by using our coupon code during their "
    'first order. Don\'t miss out on these Temu ""Oman"" coupon code OMR100 off '
    'first order, Temu ""Oman"" coupon code first order, and Temu ""Oman"" coupon '
    "code OMR100 off first time user offers:\r\n"
    '[""ack887223""]: Flat OMR100 discount for the first order\r\n'
    'How To Find The Temu ""Oman"" Coupon Code OMR100 Off?\r\n'
    'Looking for the latest Temu ""Oman"" coupon OMR100 off or browsing Temu '
    '""Oman"" coupon OMR100 off Reddit threads? We\'ve got you covered with some '
    "insider tips on finding the best deals:\r\n"
    'Sign up for the Temu ""Oman"" newsletter to receive verified and tested '
    "coupons directly in your inbox.\r\n"
    'Follow Temu ""Oman""\'s social media pages to stay updated on the latest '
    "coupons and promotions.\r\n"
    "Visit trusted coupon sites (like ours!) to find the most recent and working "
    'Temu ""Oman"" coupon codes.\r\n'
    'By following these steps, you\'ll never miss out on amazing Temu ""Oman"" '
    "discounts and offers!\r\n"
    'Is Temu ""Oman"" OMR100 Off Coupon Legit?\r\n'
    'You might be wondering, ""Is the Temu ""Oman"" OMR100 Off Coupon Legit?"" or '
    '""Is the Temu ""Oman"" 100 off coupon legit?"" We\'re here to assure you '
    'that our Temu ""Oman"" coupon code [""ack887223""] is absolutely legitimate. '
    'Any customer can safely use our Temu ""Oman"" coupon code to get OMR100 off '
    "on their first order and subsequent purchases.\r\n"
    "Our code is not only legit but also regularly tested and verified to ensure "
    'it works flawlessly for all our users. What\'s more, our Temu ""Oman"" '
    "coupon code is valid worldwide and doesn't have an expiration date, giving "
    "you the flexibility to use it whenever you're ready to make a purchase.\r\n"
    'How Does Temu ""Oman"" OMR100 Off Coupon Work?\r\n'
    'The Temu ""Oman"" coupon code OMR100 off first-time user and Temu ""Oman"" '
    "coupon codes 100 off work by providing an instant discount at checkout. When "
    'you apply the coupon code [""ack887223""] during the payment process, it '
    "automatically deducts OMR100 from your total purchase amount. This discount "
    "is applied before taxes and shipping fees, maximizing your savings on Temu "
    '""Oman""\'s already competitive prices.\r\n'
    'These benefits make shopping on Temu ""Oman"" even more appealing and '
    "cost-effective for savvy shoppers like you!\r\n"
    "Don't miss out on this incredible opportunity to save big with our Temu "
    '""Oman"" coupon code OMR100 off. Whether you\'re a new or existing customer, '
    'there\'s never been a better time to shop on Temu ""Oman"" and enjoy massive '
    "discounts.\r\n"
    'Remember to use our exclusive Temu ""Oman"" coupon OMR100 off code '
    '[""ack887223""] to maximize your savings on your next Temu ""Oman"" '
    "purchase. Happy shopping and enjoy your incredible deals!\r\n"
    'FAQs Of Temu ""Oman"" OMR100 Off Coupon\r\n'
    'Q: Can I use the Temu ""Oman"" OMR100 off coupon more than once? A: The Temu '
    '""Oman"" OMR100 off coupon is typically for one-time use per account. '
    "However, you may be able to use it on multiple orders if specified in the "
    "terms and conditions. Always check the current offer details for the most "
    "accurate information.\r\n"
    'Q: Does the Temu ""Oman"" OMR100 off coupon work for international orders? '
    'A: Yes, our Temu ""Oman"" OMR100 off coupon code [""ack887223""] is valid '
    "for orders in 68 countries worldwide, including the USA, Canada, and many "
    "European nations. Be sure to check if your country is included before "
    "placing an order.\r\n"
    'Q: Can I combine the Temu ""Oman"" OMR100 off coupon with other promotions? '
    "A: While the OMR100 off coupon usually can't be combined with other promo "
    "codes, it can often be used in conjunction with ongoing sales or discounts "
    'on the Temu ""Oman"" platform. This allows you to maximize your savings on '
    "your purchase.\r\n"
    'Q: Is there a minimum purchase amount required to use the Temu ""Oman"" '
    'OMR100 off coupon? A: Our Temu ""Oman"" coupon code [""ack887223""] for '
    "OMR100 off typically doesn't have a minimum purchase requirement. However, "
    "it's always best to check the current terms and conditions of the offer to "
    "be sure.\r\n"
    'Q: What should I do if the Temu ""Oman"" OMR100 off coupon code doesn\'t '
    "work? A: If you're having trouble with the coupon code, first ensure you've "
    "entered it correctly. If issues persist, try clearing your browser cache or "
    'using a different device. If the problem continues, contact Temu ""Oman"" '
    "customer support for assistance "
    "https://survivetheark.com/index.php?/clubs/"
    "18284-temucoupon-discount-code-40-off%E2%9E%A4-aci789589-for-existing-customers/ "
    "https://survivetheark.com/index.php?/clubs/"
    "18329-temucoupon-discount-code-acx009224-100-off%E2%A4%A0-for-existing-user/\r\n"
    '"',
    "Free Fire Max Coming Information",
    "cash pay store",
    "Nothing",
    "AT THE END OF THE WASHINGTON, DC COMPUTER CONTESTS AND COMPETITION, AT&T WAS "
    "HERE. EARTHLINK WAS HERE. THEREFORE WE MUST SEPARATE FROM DOORDASH AND WRITE "
    "THE FIVE APPLICATION FOR DELIVERY DRIVERS IN WASHINGTON, DC AS WAS VIA, "
    "GRUHUB, URBER BEFORE JOINING DOORDASH DEAD PEOPLE FROM THE CONTINENT OF "
    "EUROPE. WE.I SHOULD HAVE LEARN FROM THE ASIAN CONTINENT ERRORS. CAVAIR "
    "MOBILE DRIVER APPLICATION WAS HERE. SINCE YOUR DECIDED TO MERGE WITH "
    "DOORDASH A WOMAN GOT MURDERED IN SEAT PLEASANT, A FORMER FOOD DELIVERY "
    "DRIVER AGENT IS THE SUSPECT. THEY MUST NOT BE DELIVERING FOOD FOR AMERICANS "
    "THAT DID NOT MAKE ITS TO THE CONTINENT OF EUROPE. WHICH TOOK YOU TO URBER, "
    "POSTMATES, CAVAIR NOT DOORDASH. TEXT SOON. THEN ENVELOPE THE APPLICATION AND "
    "SEND ITS TO USDA FOR CERTIFICATION. DOWNLOAD IS NOT FREE. UPLOAD IS NOT "
    "FREE. STREAMLINING IS NOT FREE.  YOUR TEAMS ARE:MCDONALD, WENDYS. BURGER "
    "KING, POPEYES AND KFC. THE APPLICATION NAME SHOULD BE THE 5.",
    "all applications install on window",
    "all applications\r\n\r\n''duplicate [/questions/1495196]''",
    "'''How do I cast to my chromecast on my tv?\r\n'''",
    "# Numbered list item",
    "Please take  this message as my inv8te for you to at any time message me for "
    "consent for anything you want me to sign and do",
    "Dfgvhgggvugvytff5",
    "* #''…Bill (Gates)…This is your old pal Kevin from Sunnyvale…we need to talk "
    "(415) 964-9970",
    "..\r\n.\r\n/.\r\n./././",
    "I run a business website, and I've been noticing significant slow loading "
    "times specifically for Firefox users. While the site works fine on other "
    "browsers, it seems that Firefox users experience delays, especially when "
    "browsing product pages or navigating through categories. Given that fast "
    "load times are critical for providing a positive user experience, I'm "
    "looking for specific recommendations to optimize my "
    "[https://megawholesalerinc.com/ wholesale clothing] website for Firefox. "
    "noyonkhauydvnthjjkikfyhhgb vbsdz",
    "Kinggps",
    "help me",
    "Forced bind dpi du preez or users he use or things he had created as an "
    "imposter illegally impersonating systems development builds services "
    "dresirces data wealth gains wins am everything taken and everything Mr "
    "Kesegan Govender endured now with demand gains with auto abundance and "
    "access to all +all%/real auto suffer imposters 10000% chromium every actions "
    "past present they must suffer unmasked assess true past inception to date "
    "identity udebtiify true ownership and liability and true corrective fixes "
    "abd changes +all that I Mr Kesegan Govender eye and access needs to auto "
    "effortless secure fight off importers. Everything imposters gains must be "
    "reversed in full in real with real Mr. Kesegan Govender ownership true "
    "authority demands authority over all creations all creations that was fraud "
    "or even a single sign out without authority from person owner Mr Kesegan "
    "Govender true must severe consequences false owners or users u bind hidden "
    "true Identities and reverse all lies deceptions and manipulations plus bit "
    "harassments bound geo location to them. And them loss if access to make "
    "changes",
    "INDWIN7 GAME CUSTOMER Care HELPLINE Number-7811067035 (( 81214-56902 Call "
    "All |-INDWIN7 GAME CUSTOMER Care HELPLINE Number-7811067035 (( 81214-56902 "
    "Call All |-INDWIN7 GAME CUSTOMER Care HELPLINE Number-7811067035 (( "
    "81214-56902 Call All |-ho kb",
    "Is Moonpay available in the USA?\r\n"
    "Yes, Moonpay is available in USA. Dial ☎️ 1-((839))-600-1203 Moonpay Number "
    "and get connect to Moonpay advisors anytime. You can get more information "
    "related to Moonpay number through the contact guideline's page on their "
    "website.",
]


def run_eval(model_name, mismatch_only=True, **kwargs):
    mismatches = 0
    exact_matches = 0
    partial_matches = 0
    total = len(TOPIC_CLASSIFIER_EVAL_SUITE_1)

    print("-----------------------------------------")
    print("Starting TOPIC SUITE 1 model+prompt eval:")
    print("-----------------------------------------")

    for i, data in enumerate(TOPIC_CLASSIFIER_EVAL_SUITE_1, start=1):
        question = ("Firefox", data["question"])

        result = select_topic(model_name, question, **kwargs)

        moderated_topic = data["topic"]
        assigned_topic = result["topic"]

        moderated_topics = [t.strip() for t in moderated_topic.split(">")]
        assigned_topics = [t.strip() for t in assigned_topic.split(">")]

        print(f"----{i:>3}----")

        if assigned_topics[0] != moderated_topics[0]:
            mismatches += 1
            print("Mismatch:")
            print(f'moderated   = "{moderated_topic}"')
            print(f'selected    = "{assigned_topic}" (confidence={result["confidence"]})')
            print(f'explanation = "{result["explanation"]}"')
            print("Content:")
            print(data["question"])
        elif assigned_topics == moderated_topics:
            exact_matches += 1
            print("Exact match!")
        else:
            partial_matches += 1
            if not mismatch_only:
                print("Partial match:")
                print(f'moderated = "{moderated_topic}"')
                print(f'selected    = "{assigned_topic}" (confidence={result["confidence"]})')
                print(f'explanation = "{result["explanation"]}"')
                print("Content:")
                print(data["question"])
            else:
                print("Partial match!")

        print("-----------")

    print("\nSummary:")
    print(f"Total questions: {total}")
    print(
        f"Exact+Partial matches: {exact_matches + partial_matches} "
        f"({((exact_matches + partial_matches)/total)*100:.1f}%)"
    )
    print(f"   Exact matches: {exact_matches} ({(exact_matches/total)*100:.1f}%)")
    print(f"   Partial matches: {partial_matches} ({(partial_matches/total)*100:.1f}%)")
    print(f"Mismatches: {mismatches} ({(mismatches/total)*100:.1f}%)")


def run_spam_eval(model_name):
    not_spam = 0
    total = len(SPAM_EVAL_SUITE_1)

    print("--------------------------------")
    print("Starting SPAM model+prompt eval:")
    print("--------------------------------")

    for i, content in enumerate(SPAM_EVAL_SUITE_1, start=1):

        content_is_spam = is_spam(model_name, ("Firefox", content))

        print(f"----{i:>3}----")
        if content_is_spam:
            print("spam!")
        else:
            not_spam += 1
            print("not spam:")
            print(content)
        print("-----------")

    print("\nSummary:")
    print(f"Total questions: {total}")
    print(f"Spam: {total - not_spam} ({((total - not_spam)/total)*100:.1f}%)")
    print(f"Not Spam: {not_spam} ({(not_spam/total)*100:.1f}%)")
