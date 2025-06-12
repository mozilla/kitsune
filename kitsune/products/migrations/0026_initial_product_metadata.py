from django.db import migrations


PRODUCTS_WITH_METADATA = [
    {
        "title": "Firefox",
        "metadata": {
            "description": (
                "Firefox is a free and open-source web browser. It is available on Windows,"
                " macOS, and Linux. It offers many features including private browsing mode,"
                " tracking protection, a Sync feature for synchronizing bookmarks, passwords,"
                " tabs, and more across all of your devices, a free password manager, a"
                " bookmark manager for organizing your bookmarks with folders and tags, themes"
                " for customizing its look, pinned tabs, choice of vertical or horizontal tabs,"
                " a PDF editor and viewer, website translation, picture-in-picture mode, an"
                " eyedropper tool that identifies and captures colors on the web, and many"
                " add-ons and extensions."
            ),
        },
    },
    {
        "title": "Firefox for Android",
        "metadata": {
            "description": (
                "Firefox for Android is a free and open-source web browser that provides a"
                " mobile-friendly interface optimized for Android devices."
            ),
        },
    },
    {
        "title": "Firefox for iOS",
        "metadata": {
            "description": (
                "Firefox for iOS is a free and open-source web browser that provides a"
                " mobile-friendly interface optimized for iOS devices."
            ),
        },
    },
    {
        "title": "Mozilla VPN",
        "metadata": {
            "description": (
                "Mozilla VPN is a virtual private network service that protects your online"
                " privacy and security by masking your IP address, hiding your location data,"
                " and encrypting your network activity. It is supported on Windows, macOS,"
                " Android, iOS, and Linux operating systems. It has no bandwidth restrictions"
                " or throttling, uses the fast and secure Wireguard VPN protocol, supports"
                ' custom DNS, and offers a "Multi-Hop" feature that allows you to encrypt'
                " and route your internet traffic through two server locations rather than"
                " just one."
            ),
        },
    },
    {
        "title": "Firefox Relay",
        "metadata": {
            "description": (
                "Firefox Relay is a service that lets you use an email and/or phone alias"
                " instead of your real email and/or phone number when filling out online"
                " forms or signing up for services. An alias forwards your incoming emails"
                " or phone calls to your real email address or phone number. This helps"
                " protect your privacy and reduces spam by keeping your real email address"
                " or phone number hidden. You can manage your aliases, including blocking or"
                " deleting them. Firefox Relay offers a free service with a limited number"
                " of email aliases, and also a paid Premium service that offers more features"
                " like phone aliases, unlimited email aliases, and support. Relay is also"
                " available as a Firefox extension, making it easy to integrate into your web"
                " browsing experience."
            ),
        },
    },
    {
        "title": "Mozilla Monitor",
        "metadata": {
            "description": (
                "Mozilla Monitor is a service that helps users protect their online identity"
                " and data. It provides both a free service and a subscription-based service"
                " called Monitor Plus. The core function of Mozilla Monitor is to alert users"
                " about potential data breaches and data broker exposures, offering guidance"
                " on how to mitigate risks and remove personal information from data broker"
                " websites. It scans a database of known data breaches and notifies users if"
                " their email addresses or other information have been compromised. It also"
                " allows users to scan their personal information against a list of data"
                " brokers to see if it has been exposed. Monitor Plus, the subscription-based"
                " service, provides continuous monitoring for data breaches and data broker"
                " exposures, alerts users to new vulnerabilities, and automatically removes"
                " personal information from data broker websites."
            ),
        },
    },
    {
        "title": "MDN Plus",
        "metadata": {
            "description": (
                "MDN Plus is a subscription service built on top of the Mozilla Developer"
                " Network (MDN), offering premium features like notifications, collections,"
                " and offline access for a more personalized and productive web development"
                " experience. It allows users to customize their MDN Web Docs experience,"
                " including managing collections, subscribing to updates, and using MDN"
                " offline. Collections allow premium users to organize their favorite MDN"
                " content in curated collections for easy access. Notifications allow premium"
                " users to stay informed about changes to web platform technologies by"
                " subscribing to updates in the content they care about. Offline access allows"
                " premium users complete access to MDN Web Docs without an internet connection."
            ),
        },
    },
    {
        "title": "Firefox Focus",
        "metadata": {
            "description": (
                "Firefox Focus is a privacy-focused web browser designed for mobile devices"
                " (Android and iOS). Firefox Focus is designed to block online trackers,"
                " including third-party advertising, to protect users' privacy. It has a simple"
                " interface with just one tab, no bookmarks, and no saved history. When you're"
                " finished browsing, you can easily clear your session and all associated data"
                " (history, passwords, cookies) with a tap. By blocking trackers and ads, Firefox"
                " Focus helps pages load faster and reduces data usage."
            ),
        },
    },
    {
        "title": "Firefox for Enterprise",
        "metadata": {
            "description": (
                "Firefox for Enterprise is a web browser solution tailored for businesses and"
                " organizations that need robust deployment, management, and extended support."
                " It provides tools like MSI installers (for Windows), Group Policy support"
                " (Windows ADM/ADMX templates), and configuration files (like policies.json"
                " and MacOS plist files) to facilitate large-scale deployment and customization"
                " within organizations. This allows administrators to set browser policies,"
                " manage add-ons, and customize installations across multiple computers. It"
                " provides a choice between two different release channels, Rapid Release and"
                " Extended Support Release (ESR). The Rapid Release channel aligns with the"
                " standard Firefox release cycle and offers the latest features, while the ESR"
                " channel offers a longer support cycle, providing greater stability and fewer"
                " feature updates, which is beneficial for organizations that prioritize"
                " consistent browser environments and minimizing update-related compatibility"
                " issues. In essence, Firefox for Enterprise is not a separate browser, but"
                " rather the Firefox browser bundled with specific tools and support options"
                " designed to meet the needs of businesses and organizations, particularly with"
                " regard to deployment, management, and release cadence control."
            ),
        },
    },
    {
        "title": "Thunderbird",
        "metadata": {
            "description": (
                "Thunderbird is a free and open-source email client that allows users to manage"
                " multiple email accounts in one place. It's available for Windows, macOS, and"
                " Linux. Thunderbird serves as a central hub for managing multiple email"
                " accounts, supporting various providers like Gmail, Outlook, Yahoo, and more."
                " You can consolidate all your incoming messages into a single, unified inbox"
                " for easy viewing, while still identifying the account each email belongs to"
                " through color-coding. Thunderbird offers various features to help you manage"
                " your emails, including quick search, saved search folders (virtual folders),"
                " advanced filtering, message grouping, and tags. It also offers an adaptive"
                " filter that learns from your actions which types of messages are legitimate"
                " and which are junk, to help manage unwanted emails. Unlike web-based email,"
                " Thunderbird stores emails locally on your computer, allowing you to access"
                " and search them even without an internet connection. It adheres to industry"
                " standards for email, including the POP and IMAP protocols."
            ),
        },
    },
    {
        "title": "Thunderbird for Android",
        "metadata": {
            "description": (
                "Thunderbird for Android is a free and open-source email client for Android"
                " mobile devices. It provides a mobile-friendly interface optimized for Android"
                " devices that allows users to manage multiple email accounts in one place,"
                " supporting various providers like Gmail, Outlook, Yahoo, and more. You can"
                " consolidate all your incoming messages into a single, unified inbox"
                " for easy viewing, while still identifying the account each email belongs to"
                " through color-coding. It offers various features to help you manage your"
                " emails, including quick search, saved search folders (virtual folders),"
                " advanced filtering, message grouping, and tags. It also offers an adaptive"
                " filter that learns from your actions which types of messages are legitimate"
                " and which are junk, to help manage unwanted emails. Unlike web-based email,"
                " Thunderbird stores emails locally on your device, allowing you to access"
                " and search them even without an internet connection. It adheres to industry"
                " standards for email, including the POP and IMAP protocols."
            ),
        },
    },
]


def add_initial_product_metadata(apps, schema_editor):
    Product = apps.get_model("products", "Product")

    for product_data in PRODUCTS_WITH_METADATA:
        try:
            product = Product.objects.get(title=product_data["title"], is_archived=False)
        except Product.DoesNotExist:
            print(f"""Skipped product "{product_data['title']}" because it does not exist.""")
            continue
        except Product.MultipleObjectsReturned:
            print(
                f"""Skipped product "{product_data['title']}" because it has multiple objects."""
            )
            continue

        product.metadata = product_data["metadata"]
        product.save()


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0025_product_metadata"),
    ]

    operations = [
        migrations.RunPython(add_initial_product_metadata, migrations.RunPython.noop),
    ]
