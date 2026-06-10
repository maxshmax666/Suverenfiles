package dev.suveren.files;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.Settings;
import android.text.InputType;
import android.text.format.Formatter;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.MimeTypeMap;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.text.DateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public final class MainActivity extends Activity {
    private static final int REQUEST_STORAGE = 47;

    private final DateFormat dateFormat = DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT);
    private LinearLayout fileList;
    private TextView pathView;
    private TextView emptyView;
    private File currentDir;
    private PendingOperation pendingOperation;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        currentDir = Environment.getExternalStorageDirectory();
        buildUi();
        ensureStorageAccess();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (hasStorageAccess()) {
            renderDirectory(currentDir);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_STORAGE) {
            renderDirectory(currentDir);
        }
    }

    @Override
    public void onBackPressed() {
        if (currentDir != null && currentDir.getParentFile() != null) {
            renderDirectory(currentDir.getParentFile());
            return;
        }
        super.onBackPressed();
    }

    private void buildUi() {
        int bg = getColor(R.color.suveren_bg);
        int panel = getColor(R.color.suveren_panel);
        int text = getColor(R.color.suveren_text);
        int muted = getColor(R.color.suveren_muted);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(12), dp(12), dp(12), dp(12));
        root.setBackgroundColor(bg);

        TextView title = new TextView(this);
        title.setText("Suveren Files");
        title.setTextColor(text);
        title.setTextSize(24);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        root.addView(title, matchWrap());

        pathView = new TextView(this);
        pathView.setTextColor(muted);
        pathView.setTextSize(13);
        pathView.setPadding(0, dp(6), 0, dp(10));
        root.addView(pathView, matchWrap());

        LinearLayout actions = new LinearLayout(this);
        actions.setOrientation(LinearLayout.HORIZONTAL);
        actions.setGravity(Gravity.CENTER_VERTICAL);
        actions.addView(actionButton("↑", view -> goUp()));
        actions.addView(actionButton("Новая папка", view -> promptNewFolder()));
        actions.addView(actionButton("Вставить", view -> pastePending()));
        actions.addView(actionButton("Обновить", view -> renderDirectory(currentDir)));
        root.addView(actions, matchWrap());

        ScrollView scrollView = new ScrollView(this);
        scrollView.setFillViewport(true);
        scrollView.setBackgroundColor(panel);
        fileList = new LinearLayout(this);
        fileList.setOrientation(LinearLayout.VERTICAL);
        fileList.setPadding(0, dp(6), 0, dp(6));
        emptyView = new TextView(this);
        emptyView.setTextColor(muted);
        emptyView.setText("Папка пуста или нет доступа");
        emptyView.setGravity(Gravity.CENTER);
        emptyView.setPadding(dp(16), dp(40), dp(16), dp(40));
        scrollView.addView(fileList, new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        LinearLayout.LayoutParams scrollParams = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1);
        scrollParams.topMargin = dp(12);
        root.addView(scrollView, scrollParams);
        setContentView(root);
    }

    private Button actionButton(String label, View.OnClickListener listener) {
        Button button = new Button(this);
        button.setText(label);
        button.setAllCaps(false);
        button.setOnClickListener(listener);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
        params.setMargins(dp(2), 0, dp(2), 0);
        button.setLayoutParams(params);
        return button;
    }

    private void ensureStorageAccess() {
        if (hasStorageAccess()) {
            renderDirectory(currentDir);
            return;
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            new AlertDialog.Builder(this)
                    .setTitle("Нужен доступ к файлам")
                    .setMessage("Для личного файлового менеджера нужен режим «Доступ ко всем файлам». Android выдаёт его только через системные настройки.")
                    .setPositiveButton("Открыть настройки", (dialog, which) -> {
                        Intent intent = new Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION);
                        intent.setData(Uri.parse("package:" + getPackageName()));
                        startActivity(intent);
                    })
                    .setNegativeButton("Позже", null)
                    .show();
            return;
        }

        requestPermissions(new String[] {Manifest.permission.READ_EXTERNAL_STORAGE, Manifest.permission.WRITE_EXTERNAL_STORAGE}, REQUEST_STORAGE);
    }

    private boolean hasStorageAccess() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            return Environment.isExternalStorageManager();
        }
        return checkSelfPermission(Manifest.permission.READ_EXTERNAL_STORAGE) == PackageManager.PERMISSION_GRANTED;
    }

    private void renderDirectory(File directory) {
        if (directory == null) {
            directory = Environment.getExternalStorageDirectory();
        }
        currentDir = directory;
        pathView.setText(directory.getAbsolutePath());
        fileList.removeAllViews();

        File[] children = directory.listFiles();
        if (children == null || children.length == 0) {
            fileList.addView(emptyView, matchWrap());
            return;
        }

        Arrays.sort(children, Comparator
                .comparing((File file) -> !file.isDirectory())
                .thenComparing(file -> file.getName().toLowerCase(Locale.ROOT)));

        for (File child : children) {
            fileList.addView(row(child), matchWrap());
        }
    }

    private View row(File file) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.VERTICAL);
        row.setPadding(dp(14), dp(10), dp(14), dp(10));
        row.setBackgroundColor(getColor(R.color.suveren_panel));

        TextView name = new TextView(this);
        name.setText((file.isDirectory() ? "📁 " : "📄 ") + file.getName());
        name.setTextColor(getColor(R.color.suveren_text));
        name.setTextSize(16);
        name.setTypeface(Typeface.DEFAULT_BOLD);
        row.addView(name, matchWrap());

        TextView meta = new TextView(this);
        meta.setText(meta(file));
        meta.setTextColor(getColor(R.color.suveren_muted));
        meta.setTextSize(12);
        row.addView(meta, matchWrap());

        row.setOnClickListener(view -> {
            if (file.isDirectory()) {
                renderDirectory(file);
            } else {
                openFile(file);
            }
        });
        row.setOnLongClickListener(view -> {
            showFileMenu(file);
            return true;
        });
        return row;
    }

    private String meta(File file) {
        String type = file.isDirectory() ? "папка" : Formatter.formatFileSize(this, file.length());
        String modified = dateFormat.format(new Date(file.lastModified()));
        return type + " • " + modified;
    }

    private void showFileMenu(File file) {
        List<String> items = new ArrayList<>();
        if (file.isFile()) {
            items.add("Открыть");
            items.add("Поделиться");
        }
        items.add("Копировать");
        items.add("Переместить");
        items.add("Переименовать");
        items.add("Удалить");

        new AlertDialog.Builder(this)
                .setTitle(file.getName())
                .setItems(items.toArray(new String[0]), (dialog, which) -> handleMenu(file, items.get(which)))
                .show();
    }

    private void handleMenu(File file, String action) {
        switch (action) {
            case "Открыть":
                openFile(file);
                break;
            case "Поделиться":
                shareFile(file);
                break;
            case "Копировать":
                pendingOperation = new PendingOperation(file, false);
                toast("Выбрано для копирования: " + file.getName());
                break;
            case "Переместить":
                pendingOperation = new PendingOperation(file, true);
                toast("Выбрано для перемещения: " + file.getName());
                break;
            case "Переименовать":
                promptRename(file);
                break;
            case "Удалить":
                confirmDelete(file);
                break;
            default:
                break;
        }
    }

    private void openFile(File file) {
        Intent intent = new Intent(Intent.ACTION_VIEW);
        Uri uri = LocalFileProvider.uriFor(this, file);
        intent.setDataAndType(uri, mimeType(file));
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        try {
            startActivity(Intent.createChooser(intent, "Открыть файл"));
        } catch (ActivityNotFoundException error) {
            toast("Нет приложения для открытия файла");
        }
    }

    private void shareFile(File file) {
        Intent intent = new Intent(Intent.ACTION_SEND);
        Uri uri = LocalFileProvider.uriFor(this, file);
        intent.setType(mimeType(file));
        intent.putExtra(Intent.EXTRA_STREAM, uri);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        startActivity(Intent.createChooser(intent, "Поделиться файлом"));
    }

    private String mimeType(File file) {
        int dot = file.getName().lastIndexOf('.');
        if (dot >= 0 && dot < file.getName().length() - 1) {
            String ext = file.getName().substring(dot + 1).toLowerCase(Locale.ROOT);
            String type = MimeTypeMap.getSingleton().getMimeTypeFromExtension(ext);
            if (type != null) {
                return type;
            }
        }
        return "application/octet-stream";
    }

    private void promptNewFolder() {
        promptText("Новая папка", "Имя папки", "Создать", "", name -> {
            File target = new File(currentDir, sanitizeName(name));
            if (target.exists()) {
                toast("Такой файл уже есть");
                return;
            }
            if (!target.mkdir()) {
                toast("Не удалось создать папку");
                return;
            }
            renderDirectory(currentDir);
        });
    }

    private void promptRename(File file) {
        promptText("Переименовать", "Новое имя", "Сохранить", file.getName(), name -> {
            File target = new File(file.getParentFile(), sanitizeName(name));
            if (target.exists()) {
                toast("Такое имя уже занято");
                return;
            }
            if (!file.renameTo(target)) {
                toast("Не удалось переименовать");
                return;
            }
            renderDirectory(currentDir);
        });
    }

    private void confirmDelete(File file) {
        new AlertDialog.Builder(this)
                .setTitle("Удалить?")
                .setMessage(file.getAbsolutePath())
                .setPositiveButton("Удалить", (dialog, which) -> {
                    try {
                        deleteRecursively(file);
                        renderDirectory(currentDir);
                    } catch (IOException error) {
                        toast(error.getMessage());
                    }
                })
                .setNegativeButton("Отмена", null)
                .show();
    }

    private void pastePending() {
        if (pendingOperation == null) {
            toast("Сначала выберите файл или папку");
            return;
        }
        File source = pendingOperation.source;
        if (source.isDirectory() && isInside(currentDir, source)) {
            toast("Нельзя вставить папку внутрь самой себя");
            return;
        }
        File target = uniqueTarget(new File(currentDir, source.getName()));
        try {
            if (source.isDirectory()) {
                copyDirectory(source, target);
            } else {
                copyFile(source, target);
            }
            if (pendingOperation.move) {
                deleteRecursively(source);
                pendingOperation = null;
            }
            renderDirectory(currentDir);
        } catch (IOException error) {
            toast(error.getMessage());
        }
    }

    private File uniqueTarget(File candidate) {
        if (!candidate.exists()) {
            return candidate;
        }
        String name = candidate.getName();
        String base = name;
        String ext = "";
        int dot = name.lastIndexOf('.');
        if (dot > 0) {
            base = name.substring(0, dot);
            ext = name.substring(dot);
        }
        for (int i = 1; i < 1000; i++) {
            File next = new File(candidate.getParentFile(), base + " (" + i + ")" + ext);
            if (!next.exists()) {
                return next;
            }
        }
        return new File(candidate.getParentFile(), base + " (copy)" + ext);
    }

    private static void copyFile(File source, File target) throws IOException {
        try (FileChannel in = new FileInputStream(source).getChannel();
             FileChannel out = new FileOutputStream(target).getChannel()) {
            long position = 0;
            long size = in.size();
            while (position < size) {
                position += in.transferTo(position, Math.min(8L * 1024L * 1024L, size - position), out);
            }
        }
    }

    private static void copyDirectory(File source, File target) throws IOException {
        if (!target.mkdirs() && !target.isDirectory()) {
            throw new IOException("Не удалось создать папку: " + target.getName());
        }
        File[] children = source.listFiles();
        if (children == null) {
            return;
        }
        for (File child : children) {
            File childTarget = new File(target, child.getName());
            if (child.isDirectory()) {
                copyDirectory(child, childTarget);
            } else {
                copyFile(child, childTarget);
            }
        }
    }

    private static void deleteRecursively(File file) throws IOException {
        if (file.isDirectory()) {
            File[] children = file.listFiles();
            if (children != null) {
                for (File child : children) {
                    deleteRecursively(child);
                }
            }
        }
        if (!file.delete()) {
            throw new IOException("Не удалось удалить: " + file.getName());
        }
    }

    private void goUp() {
        File parent = currentDir != null ? currentDir.getParentFile() : null;
        if (parent != null) {
            renderDirectory(parent);
        }
    }

    private void promptText(String title, String hint, String positive, String value, TextCallback callback) {
        EditText input = new EditText(this);
        input.setHint(hint);
        input.setSingleLine(true);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        input.setText(value);
        input.setSelectAllOnFocus(true);
        input.setPadding(dp(16), dp(10), dp(16), dp(10));
        new AlertDialog.Builder(this)
                .setTitle(title)
                .setView(input)
                .setPositiveButton(positive, (dialog, which) -> {
                    String text = input.getText().toString().trim();
                    if (text.isEmpty()) {
                        toast("Имя не может быть пустым");
                        return;
                    }
                    callback.onText(text);
                })
                .setNegativeButton("Отмена", null)
                .show();
    }

    private static boolean isInside(File candidate, File parent) {
        try {
            String candidatePath = candidate.getCanonicalPath();
            String parentPath = parent.getCanonicalPath();
            return candidatePath.equals(parentPath) || candidatePath.startsWith(parentPath + File.separator);
        } catch (IOException error) {
            return false;
        }
    }

    private static String sanitizeName(String name) {
        return name.replace(File.separatorChar, '_').replace('\0', '_').trim();
    }

    private void toast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }

    private LinearLayout.LayoutParams matchWrap() {
        return new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private interface TextCallback {
        void onText(String text);
    }

    private static final class PendingOperation {
        private final File source;
        private final boolean move;

        private PendingOperation(File source, boolean move) {
            this.source = source;
            this.move = move;
        }
    }
}
