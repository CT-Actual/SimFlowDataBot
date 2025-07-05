import java.io.IOException;
import java.nio.file.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Stream;

/** Builds a unique Session_ID (<date>_<track>_<tag>). */
public class SessionIdBuilder {

    private static final Pattern FILENAME_PATTERN = Pattern.compile("(\\d{4}-\\d{2}-\\d{2})_([^_]+)_([^_]+).*");
    private static final Pattern ALT_FILENAME_PATTERN = Pattern.compile("([^_]+)_([^_\\s]+) (\\d{4}-\\d{2}-\\d{2}) (\\d{2}-\\d{2}-\\d{2})_([^_]+)_(\\d+).*");

    public static String build(Path sessionsRoot,
                               String date, String track,
                               String desiredTag) throws IOException {
        String base = date + "_" + track;

        if (desiredTag != null && !desiredTag.isBlank()) {
            String candidate = base + "_" + desiredTag;
            if (Files.notExists(sessionsRoot.resolve(candidate))) return candidate;

            char suffix = 'a';
            while (Files.exists(sessionsRoot.resolve(candidate + "-" + suffix))) suffix++;
            return candidate + "-" + suffix;
        }

        try (Stream<Path> s = Files.list(sessionsRoot)) {
            int max = s.map(Path::getFileName)
                       .map(Path::toString)
                       .filter(n -> n.startsWith(base + "_"))
                       .map(n -> n.substring(base.length() + 1))
                       .filter(t -> t.matches("\\d{2}"))
                       .mapToInt(Integer::parseInt)
                       .max().orElse(0);
            return String.format("%s_%02d", base, max + 1);
        }
    }

    /** Extracts the Session_ID from a filename. */
    public static String extractSessionId(String filename) {
        System.out.println("Attempting to extract session ID from: " + filename);
        Matcher matcher = FILENAME_PATTERN.matcher(filename);
        if (matcher.matches()) {
            String sessionId = matcher.group(1) + "_" + matcher.group(2) + "_" + matcher.group(3);
            System.out.println("Matched standard pattern: " + sessionId);
            return sessionId;
        }

        Matcher altMatcher = ALT_FILENAME_PATTERN.matcher(filename);
        if (altMatcher.matches()) {
            String sessionId = altMatcher.group(3) + "_" + altMatcher.group(2).replaceAll("\\s+", "") + "_" + altMatcher.group(5) + altMatcher.group(6);
            System.out.println("Matched alternative pattern: " + sessionId);
            return sessionId;
        }

        // Fallback for simple filenames - group all untagged files together
        if (!filename.contains("_")) {
            String sessionId = "untagged_session";
            System.out.println("Matched simple pattern (grouped): " + sessionId);
            return sessionId;
        }


        String[] parts = filename.split("_");
        
        // Group all "untagged_*" files into one session
        if (parts.length >= 2 && "untagged".equals(parts[0])) {
            String sessionId = "untagged_session";
            System.out.println("Matched untagged pattern (grouped): " + sessionId);
            return sessionId;
        }
        
        if (parts.length >= 3) {
            String sessionId = parts[0] + "_" + parts[1] + "_" + parts[2];
            System.out.println("Matched fallback pattern: " + sessionId);
            return sessionId;
        }
        System.err.println("Could not extract Session_ID from filename: " + filename);
        throw new IllegalArgumentException("Could not extract Session_ID from filename: " + filename);
    }
}
