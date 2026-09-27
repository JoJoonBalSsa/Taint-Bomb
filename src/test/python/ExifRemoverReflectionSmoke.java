import javax.imageio.ImageIO;
import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.File;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.BiConsumer;
import java.util.function.Predicate;

public final class ExifRemoverReflectionSmoke {
    private static final byte[] EXIF_SEGMENT = {
            (byte) 0xff, (byte) 0xe1, 0x00, 0x12,
            'E', 'x', 'i', 'f', 0x00, 0x00,
            'M', 'M', 0x00, 0x2a, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00
    };

    public static void main(String[] args) throws Exception {
        Class<?> removerClass = Class.forName(args[0]);
        Method copy = findCopy(removerClass);
        Object remover = removerClass.getDeclaredConstructor().newInstance();
        Path sourcePng = Path.of(args[1]);
        Path work = Path.of(args[2]);
        Path input = work.resolve("input-exif.jpg");
        Path outputDir = work.resolve("output");
        Path output = outputDir.resolve(input.getFileName());
        Files.createDirectories(outputDir);
        Files.deleteIfExists(input);
        Files.deleteIfExists(output);

        BufferedImage source = ImageIO.read(sourcePng.toFile());
        BufferedImage rgb = new BufferedImage(source.getWidth(), source.getHeight(), BufferedImage.TYPE_INT_RGB);
        Graphics2D graphics = rgb.createGraphics();
        graphics.setColor(Color.WHITE);
        graphics.fillRect(0, 0, rgb.getWidth(), rgb.getHeight());
        graphics.drawImage(source, 0, 0, null);
        graphics.dispose();

        Path base = work.resolve("base.jpg");
        if (!ImageIO.write(rgb, "JPEG", base.toFile())) throw new AssertionError("No JPEG writer available");
        byte[] jpeg = Files.readAllBytes(base);
        byte[] withExif = new byte[jpeg.length + EXIF_SEGMENT.length];
        System.arraycopy(jpeg, 0, withExif, 0, 2);
        System.arraycopy(EXIF_SEGMENT, 0, withExif, 2, EXIF_SEGMENT.length);
        System.arraycopy(jpeg, 2, withExif, 2 + EXIF_SEGMENT.length, jpeg.length - 2);
        Files.write(input, withExif);

        AtomicInteger callbacks = new AtomicInteger();
        Predicate<File> filter = file -> file.getName().toLowerCase(Locale.ROOT).endsWith(".jpg");
        BiConsumer<File, File> callback = (sourceFile, targetFile) -> callbacks.incrementAndGet();
        try {
            copy.invoke(remover, new File[]{input.toFile()}, outputDir.toFile(), filter, false, callback);
        } catch (InvocationTargetException e) {
            throw new AssertionError("copy threw", e.getCause());
        }

        BufferedImage result = ImageIO.read(output.toFile());
        boolean inputHasExif = contains(Files.readAllBytes(input), new byte[]{'E', 'x', 'i', 'f', 0x00, 0x00});
        boolean outputHasExif = contains(Files.readAllBytes(output), new byte[]{'E', 'x', 'i', 'f', 0x00, 0x00});
        if (!inputHasExif || outputHasExif || callbacks.get() != 1 || result == null
                || result.getWidth() != source.getWidth() || result.getHeight() != source.getHeight()) {
            throw new AssertionError("EXIF smoke failed");
        }
        System.out.printf("class=%s method=%s input_exif=%s output_exif=%s callback_count=%d dimensions=%dx%d%n",
                removerClass.getName(), copy.getName(), inputHasExif, outputHasExif, callbacks.get(),
                result.getWidth(), result.getHeight());
    }

    private static Method findCopy(Class<?> type) {
        Class<?>[] signature = {File[].class, File.class, Predicate.class, boolean.class, BiConsumer.class};
        for (Method method : type.getDeclaredMethods()) {
            if (method.getReturnType() == void.class && java.util.Arrays.equals(method.getParameterTypes(), signature)) {
                method.setAccessible(true);
                return method;
            }
        }
        throw new AssertionError("copy(File[],File,Predicate,boolean,BiConsumer) not found in " + type.getName());
    }

    private static boolean contains(byte[] haystack, byte[] needle) {
        outer: for (int i = 0; i <= haystack.length - needle.length; i++) {
            for (int j = 0; j < needle.length; j++) if (haystack[i + j] != needle[j]) continue outer;
            return true;
        }
        return false;
    }
}
