import java.util.ArrayList;

public class Ccl {
  public class Origin {
    public String filename;
    public Integer position;
    public String string;
    public Origin(String filename, Integer position, String string) {
      this.filename = filename;
      this.position = position;
      this.string = string;
    }
  }
  public class Token {
    public String type;
    public Object value;
    public Origin origin;
    public Token(String type, Object value, Origin origin) {
      this.type = type;
      this.value = value;
      this.origin = origin;
    }
  }
  public class Node {
    public String type;
    public Object value;
    public ArrayList<Node> children;
    public Origin origin;
    public Node(String type, Object value, ArrayList<Node> children, Origin origin) {
      this.type = type;
      this.value = value;
      this.children = children;
      this.origin = origin;
    }
  }

  public String[] SYMBOLS = {
    "\\", ".", "...",
    ":",
    "+", "-", "*", "/", "%",
    "(", ")", "[", "]", ",", "=",
    "==", "<", ">", "<=", ">=", "!=",
    ";"
  };

  public String[] KEYWORDS = {
    "is",
    "while",
    "if", "else",
    "and", "or",
    "return",
  };

  public class Lexer {
    String fn, s;
    int i, j;
    ArrayList<String> indent_stack;

    public Lexer(String string, String filename) {
      s = string;
      fn = filename;
    }

    public Token MakeToken() {
      return new Token(type, value, new Origin(fn, j, s));
    }
  }

  public static void main(String[] args) {
  }
}
