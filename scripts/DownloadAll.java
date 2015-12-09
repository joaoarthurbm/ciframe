import org.jsoup.*;
import org.jsoup.nodes.*;
import org.jsoup.select.*;
import java.util.HashSet;
import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.io.BufferedReader;
import java.io.FileWriter;
import java.io.FileReader;

public class DownloadAll {
    public static void main(String[] args) throws IOException {

          File file = new File(args[0]);
          BufferedReader reader = new BufferedReader(new FileReader(file));
          File out  = new File(args[0]+".songs");
          out.createNewFile();
          FileWriter fw = new FileWriter(out.getAbsoluteFile());
          BufferedWriter bw = new BufferedWriter(fw);
          
          String line;
          while ((line = reader.readLine()) != null) {

           try {
              String prefix = "http://www.cifraclub.com.br";
              String band = line.split("/")[3];
              HashSet<String> links = new HashSet<String>();
              Document doc = Jsoup.connect(line).get();
              Elements elements = doc.getElementsByTag("li");
              for (Element li : elements) {
                 Elements as = li.getElementsByTag("a");
                 for (Element a : as) { 
                    String linkHref = a.attr("href");
                    if (linkHref.contains(band)) {
                       links.add(linkHref); 
                   }
                }
              }

              for (String link : links)
                  bw.write(prefix + link + "\n");

            } catch (Exception e) {
                 System.out.println("ERRO");
            }
         }
        bw.close();  
       } 
       
}
