# Project editing instructions

## Trainers on the main website

- Follow the existing trainer cards and personal pages in `new-site/`. Use `.github/scripts/refresh-trainers.py` and the existing shared page structure; do not invent a different layout or add extra booking controls for a newly added trainer.
- Display the trainer's given name and surname only. Never display a patronymic, even when the owner's supplied biography or source link contains a full legal name. Store only the approved public name in `new-site/data/trainers.json` → `trainers[].name`, because it also supplies cards, headings, breadcrumbs, image descriptions and page metadata.
- Fera's approved public name is `Фера Кайбуллаева` (`kaibullaeva-fera`). She trains only at the Heroes club and uses the standard trainer packages. Her profile has no online booking button; retain the existing club phone contact.
- Preserve each trainer's assigned clubs, approved photographs, full biography and applicable prices. Apply individual exceptions only when the owner explicitly gives them.
