public class Easy {

  static {
    XXTable.METATABLE = new XXTable();
  }

  public static class XXObject {
    public XXTable metatable;
    public XXObject(XXTable metatable) {
      this.metatable = metatable;
    }
  }

  public static class XXNil extends XXObject {
    public static XXTable METATABLE;
    public XXNil() {
      super(METATABLE);
    }
  }

  public static class XXBool extends XXObject {
    public static XXTable METATABLE;
    public XXBool() {
      super(METATABLE);
    }
  }

  public static class XXNumber extends XXObject {
    public static XXTable METATABLE;
    public XXNumber() {
      super(METATABLE);
    }
  }

  public static class XXString extends XXObject {
    public static XXTable METATABLE;
    public XXString() {
      super(METATABLE);
    }
  }

  public static class XXTable extends XXObject {
    public static XXTable METATABLE;
    public XXTable() {
      super(METATABLE);
    }
  }

  public static class XXForm extends XXObject {
    public static XXTable METATABLE;
    public XXForm() {
      super(METATABLE);
    }
  }

  public static class XXFunction extends XXForm {
  }

  public static void main(String[] args) {
    
  }
}
