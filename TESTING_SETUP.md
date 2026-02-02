# Automation des Tests

## 1. GitHub Actions - Tests automatisés au push

Le workflow `.github/workflows/main.yml` exécute automatiquement :

✅ **Étape 1: Test** - Les tests s'exécutent d'abord
✅ **Étape 2: Build & Deploy** - Le déploiement s'exécute SEULEMENT si les tests passent

Les tests échouent = pas de déploiement

## 2. Pre-commit Hooks - Tests avant chaque commit local

### Installation initiale

```bash
bash setup-hooks.sh
```

Ou manuellement :

```bash
pip install pre-commit
pre-commit install
```

### Comportement

Chaque fois que vous exécutez `git commit`, les hooks pre-commit :
1. Exécutent tous les tests
2. Empêchent le commit si les tests échouent
3. Permettent le commit SEULEMENT si les tests réussissent

### Contourner les hooks (non recommandé)

```bash
git commit --no-verify
```

## 3. Exécuter manuellement les tests

```bash
# Tous les tests
python -m pytest tests/ -v

# Tests spécifiques
python -m pytest tests/services/ -v

# Avec couverture
python -m pytest tests/ --cov=backend --cov-report=html
```

## Résumé du flux de travail

```
Local Development
    ↓
git commit → Pre-commit Hooks (tests locaux)
    ↓ (si réussi)
git push → GitHub Actions
    ↓
Étape 1: Test (pytest)
    ↓ (si réussi)
Étape 2: Build Docker
    ↓ (si réussi)
Étape 3: Deploy to AWS App Runner
```
