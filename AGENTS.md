# Deck — development notes

## Toolchain (Fedora, remi PHP 8.3)

- PHP 8.3 via `remi-php83` module; Node 24 + npm 11 via `nodejs24`; Composer 2.x.
- Install JS deps: `npm ci`
- Install PHP deps: `composer install` (includes vendor-bin tools via `bamarni/composer-bin-plugin`)
- Build: `npm run build` (prod) / `npm run dev` (dev) / `npm run watch`
- Lint: `npm run lint`, `npm run stylelint`, `composer run lint`, `composer run cs:check`, `composer run psalm`
- Note: the repo currently ships no JS unit test files, so `npm run test` (jest) exits with "No tests found".

## Nextcloud dev server (Docker)

```
docker run -d --name nextcloud-dev -p 8081:80 \
  -v /home/twx/projects/git/nextcloud/deck:/var/www/html/apps-extra/deck \
  ghcr.io/nextcloud/nextcloud-dev-php83:latest
```

- Access: http://localhost:8081 (login `admin`/`admin`). Host port 8080 is used by open-webui.
- App assets are served from `/apps-extra/deck/...`, not `/apps/deck/...`.
- PHPUnit unit tests (needs the server for bootstrap): run inside the container:
  `docker exec -u www-data nextcloud-dev bash -lc 'cd /var/www/html/apps-extra/deck && vendor/bin/phpunit -c tests/phpunit.xml'`

## Important: OCP autoload workaround

The app's composer `autoload-dev` maps `OCP\` to the `nextcloud/ocp` stubs in
`vendor/`. When the app runs inside a Nextcloud instance, that mapping hijacks
the server's real `OCP\` namespace and causes failures (e.g. `#[Override]`
fatals in `occ`, stale interface definitions).

After every `composer install` / `composer dump-autoload`, strip those stub
mappings from the generated autoloader so `OCP\` resolves to the server:

```
python3 scripts/strip-ocp-autoload.py vendor
```

(Only touches generated files under `vendor/composer/`, which are gitignored.)
