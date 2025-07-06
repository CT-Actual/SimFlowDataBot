import java.io.IOException;
import java.io.InputStream;
import java.nio.file.*;
import java.nio.file.attribute.FileTime;
import java.security.DigestInputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.time.LocalDate;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import java.util.stream.Stream;

import static java.nio.file.StandardWatchEventKinds.*;

public class DropOffWatcher implements Runnable {
    private final Path dropOffDir = Paths.get("2025-Season3/Car_Folder/DROP-OFF");
    private final Path sessionsRoot = Paths.get("2025-Season3/Car_Folder/SESSIONS");
    private final int debounceMillis = 2_000;   // 2 s
    private final int bundleWindowMillis = 30_000;  // 30 s

    private final Map<String, Long> sessionLastModified = new ConcurrentHashMap<>();

    @Override
    public void run() {
        try {
            processExistingFiles();
        } catch (IOException e) {
            e.printStackTrace();
        }
        try (WatchService ws = FileSystems.getDefault().newWatchService()) {
            dropOffDir.register(ws, ENTRY_CREATE);

            System.out.println("Watching DROP-OFF directory: " + dropOffDir.toAbsolutePath());

            while (true) {
                WatchKey key = ws.poll(5, TimeUnit.SECONDS); // Poll with timeout
                if (key != null) {
                    for (WatchEvent<?> event : key.pollEvents()) {
                        WatchEvent.Kind<?> kind = event.kind();
                        if (kind == OVERFLOW) {
                            continue;
                        }
                        Path filename = (Path) event.context();
                        Path child = dropOffDir.resolve(filename);

                        if (filename.toString().endsWith(".done") || filename.toString().endsWith(".done.done") || filename.toString().equals("README.md")) {
                            continue;
                        }
                        try {
                            String sessionId = SessionIdBuilder.extractSessionId(child.getFileName().toString());
                            sessionLastModified.put(sessionId, System.currentTimeMillis());
                            System.out.println("Detected new file: " + filename + " for session: " + sessionId);
                        } catch (Exception e) {
                            System.err.println("Error processing file " + filename + ": " + e.getMessage());
                        }
                    }
                    key.reset();
                    Thread.sleep(debounceMillis);
                }
                // Always check for bundles ready to process
                processBundles();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void processExistingFiles() throws IOException {
        System.out.println("Processing existing files in DROP-OFF directory...");
        try (Stream<Path> stream = Files.list(dropOffDir)) {
            stream.filter(Files::isRegularFile).forEach(path -> {
                try {
                    String sessionId = SessionIdBuilder.extractSessionId(path.getFileName().toString());
                    sessionLastModified.put(sessionId, System.currentTimeMillis());
                    System.out.println("Detected existing file: " + path.getFileName() + " for session: " + sessionId);
                } catch (Exception e) {
                    System.err.println("Error processing existing file " + path.getFileName() + ": " + e.getMessage());
                }
            });
        }
        processBundles();
    }

    private void processBundles() throws IOException {
        System.out.println("Processing all detected sessions immediately...");
        for (Map.Entry<String, Long> entry : sessionLastModified.entrySet()) {
            String sessionId = entry.getKey();
            System.out.println("Processing session: " + sessionId);
            try {
                processSessionBundle(sessionId);
            } catch (Exception e) {
                System.err.println("Failed to process bundle for session " + sessionId + ": " + e.getMessage());
                e.printStackTrace();
            }
        }
        sessionLastModified.clear();
        System.out.println("Finished processing all sessions.");
    }

    private void processSessionBundle(String sessionId) throws IOException, NoSuchAlgorithmException {
        Path sessionDir = sessionsRoot.resolve(sessionId);
        Path rawDir = sessionDir.resolve("RAW");
        Path parquetDir = sessionDir.resolve("PARQUET");
        Path dbDir = sessionDir.resolve("DB");
        Path assetsDir = sessionDir.resolve("ASSETS");
        Path reportsDir = sessionDir.resolve("REPORTS");

        Files.createDirectories(rawDir);
        Files.createDirectories(parquetDir);
        Files.createDirectories(dbDir);
        Files.createDirectories(assetsDir);
        Files.createDirectories(reportsDir);

        Map<Path, String> filesToProcess = new HashMap<>();

        try (Stream<Path> stream = Files.list(dropOffDir)) {
            stream.filter(Files::isRegularFile)
                  .filter(p -> {
                      try {
                          return SessionIdBuilder.extractSessionId(p.getFileName().toString()).equals(sessionId);
                      } catch (Exception e) {
                          return false;
                      }
                  })
                  .forEach(p -> filesToProcess.put(p, p.getFileName().toString()));
        }

        if (filesToProcess.isEmpty()) {
            System.out.println("No files found for session " + sessionId + " in DROP-OFF. Skipping.");
            return;
        }

        System.out.println("Moving files to RAW/ for session: " + sessionId);
        for (Map.Entry<Path, String> entry : filesToProcess.entrySet()) {
            Path sourceFile = entry.getKey();
            Path destFile = rawDir.resolve(sourceFile.getFileName());
            Files.move(sourceFile, destFile, StandardCopyOption.REPLACE_EXISTING);
            String hash = sha256(destFile);
            System.out.println("Moved and hashed: " + destFile.getFileName() + " (SHA-256: " + hash + ")");

            String fileName = destFile.getFileName().toString();
            if (fileName.endsWith(".csv")) {
                launchPythonScript("scripts/ingest_csv.py", destFile.toAbsolutePath().toString(), sessionId);
            } else if (fileName.endsWith(".pdf") || fileName.endsWith(".png")) {
                launchPythonScript("scripts/handle_assets.py", destFile.toAbsolutePath().toString(), sessionId);
            } else if (isSetupFile(fileName)) {
                String carName = sessionsRoot.getParent().getFileName().toString();
                launchPythonScript(
                    "SimFlowSetupAgent/simflow_setup_agent.py",
                    "analyze",
                    "--file",
                    destFile.toAbsolutePath().toString(),
                    "--vehicle",
                    carName,
                    "--output",
                    "json"
                );
                moveSetupAnalysis(destFile, carName);
            }
        }

        launchPythonScript("scripts/update_toc.py", sessionId, sessionsRoot.getParent().toAbsolutePath().toString());
        launchPythonScript("scripts/archive_assets.py", sessionDir.toAbsolutePath().toString());

        Files.createFile(dropOffDir.resolve(sessionId + ".done"));
        System.out.println("Completed processing for session: " + sessionId);
    }

    private void launchPythonScript(String scriptPath, String... args) {
        try {
            Path pythonScript = Paths.get(scriptPath);
            if (!Files.exists(pythonScript)) {
                System.err.println("Python script not found: " + pythonScript.toAbsolutePath());
                return;
            }

            String osName = System.getProperty("os.name", "").toLowerCase();
            String pythonCmd = osName.contains("win") ? "python" : "python";

            ProcessBuilder pb = new ProcessBuilder(pythonCmd, pythonScript.toAbsolutePath().toString());
            pb.command().addAll(java.util.Arrays.asList(args));
            pb.inheritIO();
            System.out.println("Launching command: " + String.join(" ", pb.command()));
            Process p = pb.start();
            int exitCode = p.waitFor();
            System.out.println("Script " + scriptPath + " exited with code: " + exitCode);
        } catch (IOException | InterruptedException e) {
            System.err.println("Error launching Python script " + scriptPath + ": " + e.getMessage());
            e.printStackTrace();
        }
    }

    private boolean isSetupFile(String name) {
        String lower = name.toLowerCase();
        return lower.endsWith(".htm") || lower.endsWith(".xlsm") || lower.endsWith(".xlsx") ||
               (lower.endsWith(".csv") && lower.contains("setup"));
    }

    private void moveSetupAnalysis(Path file, String car) {
        try {
            String date = LocalDate.now().toString();
            Path destDir = Paths.get("SimFlowSetupAgent", "PROCESSED", "by_car", car, date);
            Files.createDirectories(destDir);

            String name = file.getFileName().toString();
            int idx = name.lastIndexOf('.');
            if (idx != -1) name = name.substring(0, idx);
            Path json = Paths.get("SimFlowSetupAgent", "output", name + "_analysis.json");
            if (Files.exists(json)) {
                Files.move(json, destDir.resolve(json.getFileName()), StandardCopyOption.REPLACE_EXISTING);
            }
            Files.copy(file, destDir.resolve(file.getFileName()), StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            System.err.println("Error moving setup analysis: " + e.getMessage());
        }
    }

    public static String sha256(Path file) throws IOException, NoSuchAlgorithmException {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        try (InputStream in = Files.newInputStream(file); DigestInputStream dis = new DigestInputStream(in, md)) {
            byte[] buffer = new byte[8192];
            while (dis.read(buffer) != -1) { /* stream */ }
        }
        return HexFormat.of().formatHex(md.digest());
    }

    public static void main(String[] args) {
        System.out.println("[DropOffWatcher] Starting one-shot processing...");
        DropOffWatcher watcher = new DropOffWatcher();
        try {
            watcher.processExistingFiles();
            System.out.println("[DropOffWatcher] One-shot processing completed.");
        } catch (Exception e) {
            System.err.println("[DropOffWatcher] Error during processing: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}
