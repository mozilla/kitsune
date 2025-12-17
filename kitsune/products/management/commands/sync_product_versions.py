import re
from contextlib import nullcontext

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from product_details import product_details

from kitsune.products.models import Product, Version


class Command(BaseCommand):
    help = "Sync product versions from Mozilla product-details"

    def add_arguments(self, parser):
        parser.add_argument(
            "--product",
            type=str,
            help="Sync only this product (slug). Options: firefox, firefox-enterprise, mobile, ios, thunderbird",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be changed without modifying the database",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        verbosity = options["verbosity"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be saved\n"))

        # Product configurations
        product_configs = self._get_product_configs()

        # Filter by product if specified
        if options["product"]:
            product_slug = options["product"]
            if product_slug not in product_configs:
                raise CommandError(
                    f"Unknown product: {product_slug}. "
                    f"Available: {', '.join(product_configs.keys())}"
                )
            product_configs = {product_slug: product_configs[product_slug]}

        # Sync each product
        for product_slug, config in product_configs.items():
            try:
                product = Product.objects.get(slug=product_slug, is_archived=False)
            except Product.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ Product '{product_slug}' not found or archived")
                )
                continue

            self._sync_product(product, config, dry_run, verbosity)

    def _get_product_configs(self):
        """Return configuration for each product."""
        return {
            "firefox": {
                "name": "Firefox",
                "slug_prefix": "fx",
                "version_data": product_details.firefox_versions,
                "version_key": "LATEST_FIREFOX_VERSION",
                "history_data": product_details.firefox_history_major_releases,
                "esr_keys": [],
                "esr_only": False,
            },
            "firefox-enterprise": {
                "name": "Firefox for Enterprise",
                "slug_prefix": "fx",
                "version_data": product_details.firefox_versions,
                "version_key": "LATEST_FIREFOX_VERSION",
                "history_data": product_details.firefox_history_major_releases,
                "esr_keys": ["FIREFOX_ESR", "FIREFOX_ESR115"],
                "esr_major_versions": [52, 60, 68, 78, 91, 102, 115, 128, 140],
                "esr_only": True,
            },
            "mobile": {
                "name": "Firefox for Android",
                "slug_prefix": "m",
                "version_data": product_details.mobile_versions,
                "version_key": "version",
                "history_data": product_details.firefox_history_major_releases,
                "esr_keys": [],
                "esr_only": False,
            },
            "ios": {
                "name": "Firefox for iOS",
                "slug_prefix": "ios",
                "version_data": product_details.firefox_versions,
                "version_key": "LATEST_FIREFOX_VERSION",
                "history_data": product_details.firefox_history_major_releases,
                "esr_keys": [],
                "esr_only": False,
            },
            "thunderbird": {
                "name": "Thunderbird",
                "slug_prefix": "tb",
                "version_data": product_details.thunderbird_versions,
                "version_key": "LATEST_THUNDERBIRD_VERSION",
                "history_data": product_details.thunderbird_history_major_releases,
                "esr_keys": ["THUNDERBIRD_ESR"],
                "esr_only": False,
            },
        }

    def _sync_product(self, product: Product, config: dict, dry_run: bool, verbosity: int):
        """Sync all versions for a product."""
        latest_version = config["version_data"].get(config["version_key"])
        if not latest_version:
            return

        latest_major = self._parse_major_version(latest_version)
        if latest_major is None:
            return

        if verbosity >= 1:
            self.stdout.write(f"\nSyncing {product.title} (latest: {latest_version})...")

        esr_only = config.get("esr_only", False)

        # Use transaction only if not dry-run
        context = transaction.atomic() if not dry_run else nullcontext()

        with context:
            # Only sync regular versions if not ESR-only
            if not esr_only:
                history_data = config["history_data"]
                available_versions = self._get_available_versions(history_data, latest_major)
                self._create_or_update_versions(
                    product, config, available_versions, dry_run, verbosity
                )
            self._handle_esr_versions(product, config, dry_run, verbosity)
            self._update_visibility(product, dry_run, verbosity)

    def _get_available_versions(self, history_data: dict, latest_major: int) -> list:
        """Get list of available major version numbers from history."""
        available = []
        for version_str in history_data.keys():
            major = self._parse_major_version(version_str)
            if major and major <= latest_major:
                available.append(major)
        return sorted(set(available))

    def _create_or_update_versions(
        self,
        product: Product,
        config: dict,
        available_versions: list,
        dry_run: bool,
        verbosity: int,
    ):
        """Create or update version records for a product."""
        slug_prefix = config["slug_prefix"]

        for major_version in available_versions:
            slug = f"{slug_prefix}{major_version}"
            name = f"Version {major_version}"
            min_version = float(major_version)
            max_version = float(major_version + 1)

            try:
                version = Version.objects.get(slug=slug, product=product)
                updated = version.min_version != min_version or version.max_version != max_version

                if updated:
                    if dry_run and verbosity >= 2:
                        self.stdout.write(
                            f"  Would update {slug}: "
                            f"min {version.min_version} → {min_version}, "
                            f"max {version.max_version} → {max_version}"
                        )
                    version.min_version = min_version
                    version.max_version = max_version
                    if not dry_run:
                        version.save()
                        if verbosity >= 1:
                            self.stdout.write(f"  Updated {slug}")

            except Version.MultipleObjectsReturned:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ Multiple versions found for {slug}, using first one")
                )

            except Version.DoesNotExist:
                if dry_run and verbosity >= 2:
                    self.stdout.write(f"  Would create {slug} ({name})")
                if not dry_run:
                    Version.objects.create(
                        product=product,
                        slug=slug,
                        name=name,
                        min_version=min_version,
                        max_version=max_version,
                        visible=False,
                        default=False,
                    )
                    if verbosity >= 1:
                        self.stdout.write(f"  Created {slug}")

    def _handle_esr_versions(self, product: Product, config: dict, dry_run: bool, verbosity: int):
        """Create or update ESR versions."""
        esr_keys = config.get("esr_keys", [])
        esr_major_versions = config.get("esr_major_versions", [])

        # Collect ESR major versions from keys
        esr_majors_from_keys = set()
        if esr_keys:
            version_data = config["version_data"]
            for esr_key in esr_keys:
                esr_version_str = version_data.get(esr_key)
                if esr_version_str:
                    esr_major = self._parse_major_version(esr_version_str)
                    if esr_major is not None:
                        esr_majors_from_keys.add(esr_major)

        # Combine with explicit esr_major_versions
        all_esr_majors = esr_majors_from_keys | set(esr_major_versions)

        if not all_esr_majors:
            return

        slug_prefix = config["slug_prefix"]

        for esr_major in sorted(all_esr_majors):
            slug = f"{slug_prefix}{esr_major}-esr"
            name = f"Version {esr_major} ESR"
            min_version = float(esr_major)
            max_version = float(esr_major + 1)

            try:
                version = Version.objects.get(slug=slug, product=product)
                if version.min_version != min_version or version.max_version != max_version:
                    if dry_run and verbosity >= 2:
                        self.stdout.write(
                            f"  Would update ESR {slug}: "
                            f"min {version.min_version} → {min_version}, "
                            f"max {version.max_version} → {max_version}"
                        )
                    version.min_version = min_version
                    version.max_version = max_version
                    if not dry_run:
                        version.save()
                        if verbosity >= 1:
                            self.stdout.write(f"  Updated ESR {slug}")

            except Version.MultipleObjectsReturned:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ Multiple ESR versions found for {slug}, using first one"
                    )
                )

            except Version.DoesNotExist:
                if dry_run and verbosity >= 2:
                    self.stdout.write(f"  Would create ESR {slug} ({name})")
                if not dry_run:
                    Version.objects.create(
                        product=product,
                        slug=slug,
                        name=name,
                        min_version=min_version,
                        max_version=max_version,
                        visible=True,
                        default=False,
                    )
                    if verbosity >= 1:
                        self.stdout.write(f"  Created ESR {slug}")

    def _update_visibility(self, product: Product, dry_run: bool, verbosity: int):
        """Update visibility and default flags for all versions of a product."""
        all_versions = list(Version.objects.filter(product=product).order_by("-max_version"))
        if not all_versions:
            return

        esr_versions = [v for v in all_versions if v.slug.endswith("-esr")]
        regular_versions = [v for v in all_versions if not v.slug.endswith("-esr")]
        top_10 = regular_versions[:10]

        for version in all_versions:
            should_be_visible = version in top_10 or version in esr_versions
            should_be_default = bool(regular_versions) and version == regular_versions[0]

            if version.visible != should_be_visible or version.default != should_be_default:
                changes = []
                if version.visible != should_be_visible:
                    changes.append(f"visible {version.visible} → {should_be_visible}")
                if version.default != should_be_default:
                    changes.append(f"default {version.default} → {should_be_default}")

                if dry_run and verbosity >= 2:
                    self.stdout.write(f"  Would update {version.slug}: {', '.join(changes)}")

                version.visible = should_be_visible
                version.default = should_be_default
                if not dry_run:
                    version.save()
                    if verbosity >= 2:
                        self.stdout.write(f"  Updated {version.slug}: {', '.join(changes)}")

    def _parse_major_version(self, version_str: str) -> int | None:
        """Parse major version number from version string like '143.0.4' or '140.3.1esr'."""
        match = re.match(r"^(\d+)", version_str)
        return int(match.group(1)) if match else None
