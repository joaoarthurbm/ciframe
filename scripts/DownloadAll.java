import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.HashSet;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

public class DownloadAll {
  
  
  
  public static void main(String[] args) throws IOException {
    
    int size = 25000;
    int count = 0;
    int nextFile = 0;

    File file = new File(args[0]);
    BufferedReader reader = new BufferedReader(new FileReader(file));
    File out = new File(args[0] + "_" +String.valueOf(nextFile) + ".songs");
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

        for (String link : links) {
          bw.write(prefix + link + "\n");
          count++;
        }
        if (count >= size){
          nextFile++;
          bw.close();
          out = new File(args[0] + "_" +String.valueOf(nextFile) + ".songs");
          out.createNewFile();
          fw = new FileWriter(out.getAbsoluteFile());
          bw = new BufferedWriter(fw);  
          count = 0;
        }
          

      } catch (Exception e) {
        System.out.println("ERRO");
        System.out.println(e.getMessage());
      } 
    }
    bw.close();
  }

}
