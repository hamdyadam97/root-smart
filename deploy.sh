#!/usr/bin/env bash
# نشر آخر نسخة على السيرفر: سحب الكود، المكتبات، migrate، الملفات الثابتة، ثم إعادة التشغيل.
# يُشغَّل تلقائيًا من GitHub Actions بعد كل push على main، أو يدويًا: ./deploy.sh
#
# الإعدادات الخاصة بالسيرفر توضع في ملف deploy.env بجوار هذا السكربت (غير مرفوع على git):
#   BRANCH=main
#   VENV_DIR=/home/user/root-smart/.venv
#   RESTART_CMD="sudo systemctl restart gunicorn"
set -euo pipefail

cd "$(dirname "$0")"

if [ -f deploy.env ]; then
    set -a
    . ./deploy.env
    set +a
fi

BRANCH="${BRANCH:-main}"
RESTART_CMD="${RESTART_CMD:-sudo systemctl restart gunicorn}"

if [ -z "${VENV_DIR:-}" ]; then
    for candidate in .venv venv env; do
        if [ -f "$candidate/bin/activate" ]; then
            VENV_DIR="$candidate"
            break
        fi
    done
fi

echo "==> سحب آخر كود من $BRANCH"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

if [ -n "${VENV_DIR:-}" ]; then
    echo "==> تفعيل البيئة الافتراضية $VENV_DIR"
    # shellcheck disable=SC1090
    . "$VENV_DIR/bin/activate"
fi

echo "==> تثبيت المكتبات"
pip install -q -r requirements.txt

echo "==> migrate"
python manage.py migrate --noinput

echo "==> الملفات الثابتة"
python manage.py collectstatic --noinput

echo "==> إعادة تشغيل الموقع: $RESTART_CMD"
eval "$RESTART_CMD"

echo "==> تم النشر: $(git log -1 --format='%h %s')"
