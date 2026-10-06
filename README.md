# ls-promo

Private source repository for **promo.liniyasporta.ru**.

## Structure

- `promo-site/` — files published to the web root of `promo.liniyasporta.ru`.
- `.github/workflows/bootstrap-promo-live.yml` — imports the current live promo site over HTTPS into `promo-site/`.
- `.github/workflows/deploy-promo-reg.yml` — deploys `promo-site/` to REG.RU by SFTP.

## REG.RU target

- Host: `server193.hosting.reg.ru`
- SFTP port: `22`
- User: `u3626198`
- Remote directory: `www/promo.liniyasporta.ru/`
- GitHub Actions secret required for deployment: `PROMO_REG_PASSWORD`

Automatic deployment on push will be enabled after SFTP credentials are verified on this repository.
